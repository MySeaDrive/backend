import os
import boto3
from dotenv import load_dotenv
import os
from botocore.config import Config

# Load environment variables from the .env file
load_dotenv('./secrets/.env')

# B2 setup
B2_ENDPOINT_URL = os.getenv('B2_ENDPOINT_URL')
B2_APPLICATION_KEY_ID = os.getenv('B2_APPLICATION_KEY_ID')
B2_APPLICATION_KEY = os.getenv('B2_APPLICATION_KEY')

# Set up S3 client (configured for Backblaze B2)
s3_client = boto3.client('s3',
    endpoint_url=os.getenv('B2_ENDPOINT_URL'),
    aws_access_key_id=os.getenv('B2_APPLICATION_KEY_ID'),
    aws_secret_access_key=os.getenv('B2_APPLICATION_KEY'),
    config=Config(signature_version='s3v4')
)