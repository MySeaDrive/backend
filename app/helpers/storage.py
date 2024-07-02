import os
from ..models import MediaItem
from ..helpers.db import engine
from sqlmodel import Session
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

def copy_to_storage(user_id: str, dive_id: str, filepath: str, filename: str, mime_type: str):
    raw_url = os.path.abspath(f'./uploads/raw_{filename}')

    with open(filepath, 'rb') as in_file:
        with open(raw_url, 'wb') as out_file:
            out_file.write(in_file.read())
        
    os.remove(filepath)  # Clean up the temporary file

    media_item = MediaItem(user_id=user_id,
                           filename=filename, 
                           raw_url='/test/raw.png',
                           processed_url='/test/processed.png',
                           mime_type=mime_type,
                           dive_id=dive_id)
    
    with Session(engine) as session:
        session.add(media_item)
        session.commit()
        session.refresh(media_item)
        return media_item