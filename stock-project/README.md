# Stock Project

## Project structure
```
project-name/
├── Dockerfile
├── docker-compose.yml
├── get_raw_data.py
├── util.py
├── load_env.py
├── requirements.txt
├── README.md
├── schema.sql
└── financial/
    └── api_service.py
```

## How to run
`docker-compose up --build`

This does a few things.
- Start database server and run `schema.sql` to create the `financial_data` table.
- Runs `get_raw_data.py` to ingest two weeks of financial data from [AlphaVantage](https://www.alphavantage.co/documentation/)
- Starts Uvicorn (ASGI web server) that runs the api service and expose it on port 5000.

## API choice
We use `fastapi` due to its good support for building high-performance APIs and its use of modern Python features such as async/await, type annotations, and the Pydantic
library for data validation type hints support.

## Database choice
We use PostgreSQL for good support in the containerized application and UPSERT
support. Other DB choices like MySQL would also work.

## Environment variables
DB configuration and alphavantage API key is stored securely in the local .env file
that is not checked into github. Here's an example:
```
DB_HOST = 'db'  # Docker Compose will create a hostname with the service name
DB_NAME = 'financial_data'
DB_USER = 'postgres'
DB_PASSWORD = 'password'
ALPHAVANTAGE_API_KEY = <your api key>
```

These variables get passed to Docker in `docker-compose.yml`. You can change the postgres username and password but remember to configure them accordingly when spawning up the database, in `docker-compose.yml`.

## Testing (good cases)

### Valid start and end dates for IBM with no pagination.
`curl -X GET 'http://localhost:5000/api/financial_data?start_date=2023-07-05&end_date=2023-07-06&symbol=IBM'`
```
{"data":[{"symbol":"IBM","date":"2023-07-06","open_price":133.24,"close_price":132.16,"volume":3479032},{"symbol":"IBM","date":"2023-07-05","open_price":133.32,"close_price":134.24,"volume":2955870}],"pagination":{"count":2,"page":1,"limit":5,"pages":1},"info":{"error":""}}
```
### End date is not given.
`curl -X GET 'http://localhost:5000/api/financial_data?start_date=2023-07-06&symbol=IBM'`
```
{"data":[{"symbol":"IBM","date":"2023-07-06","open_price":133.24,"close_price":132.16,"volume":3479032}],"pagination":{"count":1,"page":1,"limit":5,"pages":1},"info":{"error":""}}
```
### Start date is not given.
`curl -X GET 'http://localhost:5000/api/financial_data?end_date=2023-02-25&symbol=IBM'`
```
{"data":[{"symbol":"IBM","date":"2023-02-14","open_price":137.05,"close_price":136.01,"volume":3202172},{"symbol":"IBM","date":"2023-02-13","open_price":136.0,"close_price":137.35,"volume":4403015},{"symbol":"IBM","date":"2023-02-10","open_price":133.78,"close_price":135.6,"volume":5049571}],"pagination":{"count":3,"page":1,"limit":5,"pages":1},"info":{"error":""}}
```
### No date is not given.
`curl -X GET 'http://localhost:5000/api/financial_data?symbol=IBM'`
```
{"data":[{"symbol":"IBM","date":"2023-07-06","open_price":133.24,"close_price":132.16,"volume":3479032},{"symbol":"IBM","date":"2023-07-05","open_price":133.32,"close_price":134.24,"volume":2955870},{"symbol":"IBM","date":"2023-07-03","open_price":133.42,"close_price":133.67,"volume":1477149},{"symbol":"IBM","date":"2023-06-30","open_price":134.69,"close_price":133.81,"volume":4236677},{"symbol":"IBM","date":"2023-06-29","open_price":131.75,"close_price":134.06,"volume":3639836}],"pagination":{"count":13,"page":1,"limit":5,"pages":3},"info":{"error":""}}
```
### No token is given
`curl -X GET 'http://localhost:5000/api/financial_data?start_date=2023-02-10&end_date=2023-02-14&limit=3&page=2'`
```
{"data":[{"symbol":"AAPL","date":"2023-02-13","open_price":150.95,"close_price":153.85,"volume":62199013},{"symbol":"IBM","date":"2023-02-10","open_price":133.78,"close_price":135.6,"volume":5049571},{"symbol":"AAPL","date":"2023-02-10","open_price":149.46,"close_price":151.01,"volume":57450708}],"pagination":{"count":6,"page":2,"limit":3,"pages":2},"info":{"error":""}}
```

### No token, no date
`curl -X GET 'http://localhost:5000/api/financial_data'`
```
{"data":[{"symbol":"AAPL","date":"2023-07-06","open_price":189.84,"close_price":191.81,"volume":44995399},{"symbol":"IBM","date":"2023-07-06","open_price":133.24,"close_price":132.16,"volume":3479032},{"symbol":"IBM","date":"2023-07-05","open_price":133.32,"close_price":134.24,"volume":2955870},{"symbol":"AAPL","date":"2023-07-05","open_price":191.57,"close_price":191.33,"volume":46920261},{"symbol":"IBM","date":"2023-07-03","open_price":133.42,"close_price":133.67,"volume":1477149}],"pagination":{"count":26,"page":1,"limit":5,"pages":6},"info":{"error":""}}
```

### Pagination with limit
`curl -X GET 'http://localhost:5000/api/financial_data?symbol=IBM&limit=100&page=1'`
```
Large output omitted
...
"pagination":{"count":13,"page":1,"limit":100,"pages":1},
...
```

### Pagination with page
`curl -X GET 'http://localhost:5000/api/financial_data?symbol=IBM&limit=1&page=3'`
```
{"data":[{"symbol":"IBM","date":"2023-07-03","open_price":133.42,"close_price":133.67,"volume":1477149}],"pagination":{"count":13,"page":3,"limit":1,"pages":13},"info":{"error":""}}
```

### Get statistics with valid dates and symbol
`curl -X GET 'http://localhost:5000/api/statistics?start_date=2023-07-01&end_date=2023-07-06&symbol=IBM'`
```
{"data":{"start_date":"2023-07-01","end_date":"2023-07-06","symbol":"IBM","average_daily_open_price":133.32666666666665,"average_daily_close_price":133.35666666666665,"average_daily_volume":2647034},"info":{"error":""}}
```


## Testing (error handling)
### Invalid date string
`curl -X GET 'http://localhost:5000/api/financial_data?start_date=2023-0-10&limit=3&page=2'`
```
{"data":[],"pagination":null,"info":{"error":"Input start or end date is invalid"}}
```

### Non existing symbol
`curl -X GET 'http://localhost:5000/api/financial_data?symbol=noexist'`
```
{"data":[],"pagination":{"count":0,"page":1,"limit":5,"pages":0},"info":{"error":""}}
```

### End date before start date
`curl -X GET 'http://localhost:5000/api/financial_data?end_date=2023-07-05&start_date=2023-07-06&symbol=IBM'`
```
{"data":[],"pagination":null,"info":{"error":"Input end date is before start date"}}
```

### Empty response for statistics
`curl -X GET 'http://localhost:5000/api/statistics?start_date=2023-01-01&end_date=2023-01-31&symbol=IBM'`
```
{"data":null,"info":{"error":"No data found for given parameters."}}
```

### Missing symbol
`curl -X GET 'http://localhost:5000/api/statistics?start_date=2023-01-01&end_date=2023-01-31'`
```
{"data":null,"info":{"error":"Symbol is not specified"}}
```

### Missing start or end date
`curl -X GET 'http://localhost:5000/api/statistics?start_date=2023-01-01&symbol=IBM'`
```
{"data":null,"info":{"error":"Input end date is invalid"}}
```

`curl -X GET 'http://localhost:5000/api/statistics?end_date=2023-01-01&symbol=IBM'`
```
{"data":null,"info":{"error":"Input start date is invalid"}}
```


## Backfill
It is possible to backfill older data by setting today to a particular date in the past. For example, setting
`today = datetime.date(2023, 2, 14)` will backfill two weeks of data ending Feb 14.