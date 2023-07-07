import os
from dotenv import load_dotenv


# Load .env file
load_dotenv()

API_KEY = os.getenv('ALPHAVANTAGE_API_KEY')
DATABASE = {
    'name': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST')
}
