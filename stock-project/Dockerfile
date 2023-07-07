FROM python:3.8

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run data ingestion script and api service
CMD python get_raw_data.py && uvicorn financial.api_service:app --host 0.0.0.0 --port 5000
