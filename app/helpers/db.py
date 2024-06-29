from sqlmodel import create_engine
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv('./secrets/.env')

# Get the database connection parameters from environment variables
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
database = os.getenv('DB_NAME')

# Create the engine
engine = create_engine(f'postgresql://{username}:{password}@{host}:{port}/{database}')