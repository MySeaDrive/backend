from fastapi import APIRouter, Depends, HTTPException
from ..helpers.storage import get_s3_client, delete_file_from_storage
from ..models import MediaItem, UploadUrlsRequest, User, NewMediaItem, Dive, MediaItemState
from ..helpers.db import engine
from ..helpers.auth import get_current_user
from sqlmodel import Session, select
from typing import Dict
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os
from uuid import uuid4
from ..jobs.thumbnail_generator import generate_thumbnails
from ..jobs.color_corrector import color_correct_media
from ..queue_setup import thumbnail_queue, color_correction_queue

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
                        state=MediaItemState.PROCESSING,
                        dive_id=dive_id)
        session.add(media_item)
        session.commit()
        session.refresh(media_item)

        # Enqueue thumbnail generation job
        thumbnail_queue.enqueue(generate_thumbnails, media_item.id)

        # Enqueue color correction job
        color_correction_queue.enqueue(color_correct_media, media_item.id, job_timeout=600)


        return media_item
    
@media_items_router.delete('/{id}')
async def delete_media_item(id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        media_item = session.get(MediaItem, id)
        if not media_item or media_item.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Media item not found")
        
        # Delete the file from storage
        delete_file_from_storage(media_item.raw_url, current_user.id)
        if media_item.processed_url and media_item.processed_url != media_item.raw_url:
            delete_file_from_storage(media_item.processed_url, current_user.id)
        
        # Delete thumbnails
        if media_item.thumbnails:
            for thumbnail in media_item.thumbnails:
                delete_file_from_storage(thumbnail, current_user.id)
        
        session.delete(media_item)
        session.commit()
        
        return {"message": "Media item deleted successfully"}

@media_items_router.patch('/{id}/move')
async def move_media_item(id: int, new_dive_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        media_item = session.get(MediaItem, id)
        if not media_item or media_item.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Media item not found")
        
        new_dive = session.get(Dive, new_dive_id)
        if not new_dive or new_dive.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Destination dive not found")
        
        media_item.dive_id = new_dive_id
        session.add(media_item)
        session.commit()
        session.refresh(media_item)
        
        return media_item