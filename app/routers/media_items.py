from fastapi import APIRouter, Depends, HTTPException
from ..helpers.storage import s3_client
from ..models import MediaItem, UploadUrlsRequest, User, NewMediaItem
from ..helpers.db import engine
from ..helpers.auth import get_current_user
from sqlmodel import Session, select
from typing import Dict
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os
from uuid import uuid4

# Load environment variables from the .env file
load_dotenv('./secrets/.env')

media_items_router = APIRouter(prefix='/media', tags=["Media Items"])

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
                    'Key': f"{uuid4()}_raw{os.path.splitext(file.name)[1]}",
                    'ContentType': file.content_type
                },
                ExpiresIn=3600  # URL valid for 1 hour
            )
            upload_urls[file.id] = presigned_url
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate presigned URL: {str(e)}")

    return upload_urls

@media_items_router.post('/save')
async def save(new_media_item: NewMediaItem, dive_id:int = None, current_user: User = Depends(get_current_user)) -> MediaItem:

    with Session(engine) as session:
        media_item = MediaItem(user_id=current_user.id,
                        filename=new_media_item.filename, 
                        raw_url=new_media_item.raw_url,
                        processed_url=new_media_item.raw_url, # Same for now as raw
                        mime_type=new_media_item.mime_type,
                        dive_id=dive_id)
        session.add(media_item)
        session.commit()
        session.refresh(media_item)
        return media_item