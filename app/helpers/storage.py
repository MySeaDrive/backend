import os
import boto3
from dotenv import load_dotenv
import os
from botocore.config import Config
from urllib.parse import urlparse
from uuid import UUID

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

def delete_file_from_b2(file_url: str, user_id: UUID):
    parsed_url = urlparse(file_url)
    file_key = f"user-{user_id}/{parsed_url.path.split('/')[-1]}"

    try:
        s3_client.delete_object(Bucket=os.getenv("B2_BUCKET"), Key=file_key)
    except Exception as e:
        print(f"Error deleting file from B2: {str(e)}")