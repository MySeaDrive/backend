import os
import boto3
from dotenv import load_dotenv
import os
from botocore.config import Config
from urllib.parse import urlparse
from uuid import UUID

# Load environment variables from the .env file
load_dotenv('./secrets/.env')

# Storage setup
STORAGE_ENDPOINT_URL = os.getenv('STORAGE_ENDPOINT_URL')
STORAGE_APPLICATION_KEY_ID = os.getenv('STORAGE_APPLICATION_KEY_ID')
STORAGE_APPLICATION_KEY = os.getenv('STORAGE_APPLICATION_KEY')

def get_s3_client():
    # Set up S3 client
    return boto3.client('s3',
        endpoint_url=os.getenv('STORAGE_ENDPOINT_URL'),
        aws_access_key_id=os.getenv('STORAGE_APPLICATION_KEY_ID'),
        aws_secret_access_key=os.getenv('STORAGE_APPLICATION_KEY'),
        config=Config(signature_version='s3v4')
    )

def upload_file_to_storage(file_obj, file_key):
    s3_client = get_s3_client()
    s3_client.upload_fileobj(file_obj, os.getenv("STORAGE_BUCKET"), file_key)

def delete_file_from_storage(file_url: str, user_id: UUID):
    parsed_url = urlparse(file_url)
    file_key = f"user-{user_id}/{parsed_url.path.split('/')[-1]}"

    try:
        get_s3_client().delete_object(Bucket=os.getenv("STORAGE_BUCKET"), Key=file_key)
    except Exception as e:
        print(f"Error deleting file from storage: {str(e)}")