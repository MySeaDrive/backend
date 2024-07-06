from fastapi import APIRouter, Depends, HTTPException
from ..helpers.storage import get_s3_client
from ..models import MediaItem, UploadUrlsRequest, User, NewMediaItem
from ..helpers.db import engine
from ..helpers.auth import get_current_user
from sqlmodel import Session, select
from typing import Dict
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os
from uuid import uuid4
from ..jobs.thumbnail_generator import generate_thumbnails
from ..queue_setup import thumbnail_queue

# Load environment variables from the .env file
load_dotenv('./secrets/.env')

media_items_router = APIRouter(prefix='/media', tags=["Media Items"])

@media_items_router.post('/get_upload_urls')
async def get_upload_urls(request: UploadUrlsRequest, current_user: User = Depends(get_current_user)) -> Dict[str, str]:
    bucket_name = os.getenv("STORAGE_BUCKET")
    
    upload_urls = {}
    for file in request.files:
        try:
            file_key = f"user-{current_user.id}/{uuid4()}_raw{os.path.splitext(file.name)[1]}"
            presigned_url = get_s3_client().generate_presigned_url('put_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': file_key,
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

    storage_endpoint = os.getenv('STORAGE_ENDPOINT_URL')
    bucket_name = os.getenv("STORAGE_BUCKET")
    folder_name = f"user-{current_user.id}"
    file_key = new_media_item.pre_signed_url.split('?')[0].split('/')[-1]  # Extract file key from the pre-signed URL
    
    # Construct the public URL
    public_url = f"{storage_endpoint}/{bucket_name}/{folder_name}/{file_key}"


    with Session(engine) as session:
        media_item = MediaItem(user_id=current_user.id,
                        filename=new_media_item.filename, 
                        raw_url=public_url,
                        processed_url=public_url, # Same for now as raw
                        mime_type=new_media_item.mime_type,
                        dive_id=dive_id)
        session.add(media_item)
        session.commit()
        session.refresh(media_item)

        # Enqueue thumbnail generation job
        thumbnail_queue.enqueue(generate_thumbnails, media_item.id)

        return media_item