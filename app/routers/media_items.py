from fastapi import APIRouter, UploadFile, BackgroundTasks, Depends, HTTPException
from tempfile import NamedTemporaryFile
from ..helpers.storage import copy_to_storage, s3_client
from ..models import MediaItem, UploadUrlsRequest, User
from ..helpers.db import engine
from ..helpers.auth import get_current_user
from sqlmodel import Session, select
from typing import Dict
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv('./secrets/.env')

media_items_router = APIRouter(prefix='/media', tags=["Media Items"])

@media_items_router.post('/upload')
async def upload(file: UploadFile, background_tasks: BackgroundTasks, dive: int | None = None):

    # Save the file temporarily
    with NamedTemporaryFile(delete=False) as temp_file:
        contents = await file.read()
        temp_file.write(contents)
        temp_file_path = temp_file.name

    # Schedule the storage upload task to run in the background
    user_id = None
    background_tasks.add_task(copy_to_storage, user_id, dive, temp_file_path, file.filename, file.content_type)

    return {'Info': 'Uploaded'}

@media_items_router.get('/list')
async def list_all_items() -> list[MediaItem]:

    with Session(engine) as session:
        query = select(MediaItem)
        media_items = session.exec(query).all()
        return media_items

@media_items_router.post('/get_upload_urls')
async def get_upload_urls(request: UploadUrlsRequest, current_user: User = Depends(get_current_user)) -> Dict[str, str]:
    bucket_name = f"user-{current_user.id}"
    
    # Check if the bucket exists, if not create it
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError:
        try:
            s3_client.create_bucket(Bucket=bucket_name)
            
            # Set CORS configuration
            cors_configuration = {
                'CORSRules': [{
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE'],
                    'AllowedOrigins': [os.getenv('FRONTEND_URL', 'http://localhost:3000')],
                    'ExposeHeaders': ['ETag']
                }]
            }
            s3_client.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=cors_configuration)
            
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Failed to create bucket: {str(e)}")

    upload_urls = {}
    for file in request.files:
        try:
            presigned_url = s3_client.generate_presigned_url('put_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': file.name,
                    'ContentType': file.content_type
                },
                ExpiresIn=3600  # URL valid for 1 hour
            )
            upload_urls[file.id] = presigned_url
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate presigned URL: {str(e)}")

    return upload_urls