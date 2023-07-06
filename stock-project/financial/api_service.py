from fastapi import FastAPI, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from math import ceil

DATABASE = {
    'name': 'financial_data',
    'user': 'postgres',
    'password': 'securepassword',
    'host': 'db'
}

app = FastAPI()

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

class FinancialDataResponse(BaseModel):
    data: List[FinancialData]
    pagination: Pagination
    info: Optional[str] = None

class StatisticsData(BaseModel):
    start_date: str
    end_date: str
    symbol: str
    average_daily_open_price: float
    average_daily_close_price: float
    average_daily_volume: int

class StatisticsResponse(BaseModel):
    data: StatisticsData
    info: Optional[str] = None

@app.get("/api/financial_data", response_model=FinancialDataResponse)
async def read_financial_data(start_date: Optional[str] = None, 
                               end_date: Optional[str] = None, 
                               symbol: Optional[str] = None, 
                               limit: int = 5, page: int = 1):
    with psycopg2.connect(database=DATABASE['name'], user=DATABASE['user'], password=DATABASE['password'], host=DATABASE['host']) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = "SELECT * FROM financial_data"
            conditions = []

            if start_date is not None:
                conditions.append(f"date >= '{start_date}'")

            if end_date is not None:
                conditions.append(f"date <= '{end_date}'")

            if symbol is not None:
                conditions.append(f"symbol = '{symbol}'")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            cur.execute(query)
            total_count = cur.rowcount
            pages = ceil(total_count / limit)

            query += f" OFFSET {(page - 1) * limit} LIMIT {limit}"
            cur.execute(query)
            rows = cur.fetchall()

            data = [dict(row) for row in rows]

    return {"data": data, "pagination": {"count": total_count, "page": page, "limit": limit, "pages": pages}, "info": ""}

@app.get("/api/statistics", response_model=StatisticsResponse)
async def read_statistics(start_date: str, end_date: str, symbol: str):
    with psycopg2.connect(database=DATABASE['name'], user=DATABASE['user'], password=DATABASE['password'], host=DATABASE['host']) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = f"SELECT AVG(open_price) as average_daily_open_price, AVG(close_price) as average_daily_close_price, AVG(volume) as average_daily_volume FROM financial_data WHERE date >= '{start_date}' AND date <= '{end_date}' AND symbol = '{symbol}'"
            cur.execute(query)
            row = cur.fetchone()

            if row is None:
                raise HTTPException(status_code=404, detail="Symbol not found")

            data = {
                'start_date': start_date,
                'end_date': end_date,
                'symbol': symbol,
                'average_daily_open_price': row['average_daily_open_price'],

