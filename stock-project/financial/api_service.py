from fastapi import FastAPI
from typing import List, Optional
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

import util
from load_env import DATABASE

app = FastAPI()
database_name = DATABASE['name']
date_format = 'YYYY-MM-DD'

# Model defnitions


class FinancialData(BaseModel):
    symbol: str
    date: str
    open_price: float
    close_price: float
    volume: int


class Pagination(BaseModel):
    count: int
    page: int
    limit: int
    pages: int


class Info(BaseModel):
    error: str


class FinancialDataResponse(BaseModel):
    data: Optional[List[FinancialData]] = []
    pagination: Pagination = None
    info: Info = None


class StatisticsData(BaseModel):
    start_date: str
    end_date: str
    symbol: str
    average_daily_open_price: float
    average_daily_close_price: float
    average_daily_volume: int


class StatisticsResponse(BaseModel):
    data: Optional[StatisticsData] = None
    info: Info = None


# API definitions
@app.get("/api/financial_data", response_model=FinancialDataResponse)
async def read_financial_data(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        symbol: Optional[str] = None, limit: int = 5, page: int = 1):
    """
    This asynchronous endpoint retrieves financial data records from the database.

    Parameters:
    start_date (str, optional): The starting date of the data retrieval in the format 'YYYY-MM-DD'. Defaults to None.
    end_date (str, optional): The ending date of the data retrieval in the format 'YYYY-MM-DD'. Defaults to None.
    symbol (str, optional): The stock symbol to filter data. Defaults to None.
    limit (int, optional): The maximum number of records to return per page. Defaults to 5.
    page (int, optional): The page number to return. Defaults to 1.

    Returns:
    A dictionary containing the data, pagination information and any error information.
    """

    try:
        # Connect to the database
        with psycopg2.connect(
                database=DATABASE['name'], user=DATABASE['user'],
                password=DATABASE['password'], host=DATABASE['host'],
                cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                # Some basic validation
                if limit <= 0:
                    return {
                        "data": [],
                        "pagination": None,
                        "info": {"error": "Input limit is invalid"}
                    }
                if page < 0:
                    return {
                        "data": [],
                        "pagination": None,
                        "info": {"error": "Input page is invalid"}
                    }
                if start_date and not util.is_date(start_date):
                    return {
                        "data": [],
                        "pagination": None,
                        "info": {"error": "Input start date is invalid"}
                    }
                if end_date and not util.is_date(end_date):
                    return {
                        "data": [],
                        "pagination": None,
                        "info": {"error": "Input end date is invalid"}
                    }
                if start_date and end_date and not util.is_date_after(
                        start_date, end_date):
                    return {"data": [], "pagination": None, "info": {
                        "error": "Input end date is before start date"}}

                # Query to get the total count of records
                count_query = f"SELECT COUNT(*) FROM {database_name}"
                if symbol:
                    count_query += f" WHERE symbol = '{symbol}'"
                else:
                    count_query += f" WHERE symbol LIKE '%'"

                # Handle date clause for count query
                if start_date:
                    count_query += f" AND date >= '{start_date}'"
                if end_date:
                    count_query += f" AND date <= '{end_date}'"

                cur.execute(count_query)
                count = cur.fetchone()['count']

                # Main query to get the records with pagination
                query = f"SELECT symbol, to_char(date, 'YYYY-MM-DD') as date, open_price, close_price, volume FROM {database_name}"
                if symbol:
                    query += f" WHERE symbol = '{symbol}'"
                else:
                    query += f" WHERE symbol LIKE '%'"
                # Handle date query clause for record query
                if start_date:
                    query += f" AND date >= '{start_date}'"
                if end_date:
                    query += f" AND date <= '{end_date}'"
                # Handle pagination
                query += f" ORDER BY date DESC LIMIT {limit} OFFSET {(page - 1) * limit}"

                cur.execute(query)
                result = cur.fetchall()
                return {
                    "data": result,
                    "pagination": {
                        "count": count,
                        "page": page,
                        "limit": limit,
                        "pages": (count // limit) + (1 if count % limit > 0 else 0)
                    },
                    "info": {"error": ""}
                }
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error while executing PostgreSQL query", error)


@app.get("/api/statistics", response_model=StatisticsResponse)
async def read_statistics(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        symbol: Optional[str] = None):
    """
    This asynchronous endpoint retrieves statistics on financial data for a specific symbol over a given period of time.

    Parameters:
    start_date (str, optional): The starting date of the data retrieval in the format 'YYYY-MM-DD'. Defaults to None.
    end_date (str, optional): The ending date of the data retrieval in the format 'YYYY-MM-DD'. Defaults to None.
    symbol (str, optional): The stock symbol to filter data. Defaults to None.

    Returns:
    A dictionary containing the calculated statistic results and any error information.
    """

    try:
        # Connect to the database
        with psycopg2.connect(
                database=DATABASE['name'], user=DATABASE['user'],
                password=DATABASE['password'], host=DATABASE['host'],
                cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                # Some basic validation. For this api, all inputs are required.
                if not util.is_date(start_date):
                    return {
                        "data": None,
                        "info": {"error": "Input start date is invalid"}
                    }

                if not util.is_date(end_date):
                    return {
                        "data": None,
                        "info": {"error": "Input end date is invalid"}
                    }

                if not util.is_date_after(start_date, end_date):
                    return {
                        "data": None, "info": {
                            "error": "Input end date is before start date"}}

                if not symbol:
                    return {
                        "data": None,
                        "info": {"error": "Symbol is not specified"}
                    }

                query = f"""
                    SELECT
                        symbol,
                        AVG(open_price::decimal) as average_daily_open_price,
                        AVG(close_price::decimal) as average_daily_close_price,
                        AVG(volume::decimal) as average_daily_volume
                    FROM {database_name}
                    WHERE date BETWEEN '{start_date}' AND '{end_date}' AND symbol='{symbol}'
                    GROUP BY symbol;
                """
                cur.execute(query)
                # Fetch the results
                result = cur.fetchone()
                if result is None:
                    return {
                        "data": None, "info": {
                            "error": "No data found for given parameters."}}

                return {
                    "data": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "symbol": result['symbol'],
                        "average_daily_open_price": float(
                            result['average_daily_open_price']),
                        "average_daily_close_price": float(
                            result['average_daily_close_price']),
                        "average_daily_volume": float(
                            result['average_daily_volume'])},
                    "info": {
                        "error": ""}}
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error while executing PostgreSQL query", error)
