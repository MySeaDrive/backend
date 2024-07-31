from sqlmodel import create_engine
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv('./secrets/.env')

# Get the database connection parameters from environment variables
connection_string = os.getenv('DB_CONNECTION_STRING')

# Create the engine
engine = create_engine(connection_string)