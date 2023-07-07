import requests
import datetime
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

from load_env import DATABASE, API_KEY


today = datetime.date.today()
# today = datetime.date(2023, 2, 14)


def get_stock_data(symbol):
    base_url = "https://www.alphavantage.co/query?"
    # Create the query string
    function = 'TIME_SERIES_DAILY_ADJUSTED'
    datatype = 'json'
    query_string = f'{base_url}function={function}&symbol={symbol}&apikey={API_KEY}&datatype={datatype}'

    # Make the request
    response = requests.get(query_string)

    # Parse the JSON response
    data = response.json()

    # Basic error handling
    if 'Error Message' in data:
        raise ValueError(data['Error Message'])

    # Get the time series data
    stock_data = data['Time Series (Daily)']

    return stock_data

def get_recent_two_weeks_data(stock_data, symbol):
    # Get today's date

    # Calculate the date two weeks ago
    two_weeks_ago = today - datetime.timedelta(weeks=2)

    # Process the raw API data response
    two_weeks_data = [{
        'symbol': symbol,
        'date': date,
        'open_price': stock_data[date]['1. open'],
        'close_price': stock_data[date]['4. close'],
        'volume': stock_data[date]['6. volume']}
        for date in stock_data if two_weeks_ago <= datetime.datetime.strptime(date, '%Y-%m-%d').date() <= today]

    return two_weeks_data

def upsert_to_db(data):
    # Connect to your postgres DB
    conn = psycopg2.connect(
            dbname=DATABASE['name'], user=DATABASE['user'],
            password=DATABASE['password'], host=DATABASE['host'])
    cur = conn.cursor()

    # Prepare the SQL statement. For dedup, use the combination of date and symbol
    # as a unique constraint and then use ON CONFLICT clause to update the record
    # if it already exists.

    sql = """
        INSERT INTO financial_data (symbol, date, open_price, close_price, volume) 
        VALUES %s
        ON CONFLICT (symbol, date)
        DO UPDATE SET
        open_price = EXCLUDED.open_price,
        close_price = EXCLUDED.close_price,
        volume = EXCLUDED.volume;
    """
    print(f'Executing sql query: {sql}')
    execute_values(cur, sql, data)

    # Commit the changes and close the connection
    conn.commit()
    cur.close()
    conn.close()


def main():
    stocks = ['IBM', 'AAPL']
    all_data = []

    for stock in stocks:
        # Get the stock data
        stock_data = get_stock_data(stock)

        # Get the data for the last two weeks
        two_weeks_data = get_recent_two_weeks_data(stock_data, stock)

        all_data.extend(two_weeks_data)

    # Insert the data to the SQLite database
    all_data = [tuple(d.values()) for d in all_data]
    upsert_to_db(all_data)

if __name__ == "__main__":
    main()

