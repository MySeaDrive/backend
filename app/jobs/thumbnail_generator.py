import cv2
from PIL import Image
from io import BytesIO
import requests
import os
from uuid import uuid4, UUID
from typing import List
from sqlmodel import Session
from ..models import MediaItem
from ..helpers.db import engine
from ..helpers.storage import upload_file_to_storage
import numpy as np

def generate_thumbnails(media_item_id: int):
    with Session(engine) as session:
        media_item = session.get(MediaItem, media_item_id)
        if not media_item:
            return
        
        if media_item.mime_type.startswith('image/'):
            thumbnails = [generate_image_thumbnail(media_item.raw_url)]
        elif media_item.mime_type.startswith('video/'):
            thumbnails = generate_video_thumbnails(media_item.raw_url)
        else:
            return  # Unsupported media type
        
        # Upload thumbnails to storage
        thumbnail_urls = upload_thumbnails_to_storage(thumbnails, media_item.user_id, media_item_id)
        
        # Update media_item with thumbnail URLs
        media_item.thumbnails = thumbnail_urls
        session.commit()

def generate_image_thumbnail(image_url: str) -> Image:
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    
    # Calculate aspect ratio
    aspect_ratio = img.width / img.height
    
    if aspect_ratio > 16/9:  # Wider than 16:9
        new_width = 640
        new_height = int(640 / aspect_ratio)
    else:  # Taller than 16:9
        new_height = 360
        new_width = int(360 * aspect_ratio)
    
    # Resize maintaining aspect ratio
    img = img.resize((new_width, new_height), Image.LANCZOS)
    
    # Create a new image with padding
    new_img = Image.new("RGB", (640, 360), (0, 0, 0))
    paste_x = (640 - new_width) // 2
    paste_y = (360 - new_height) // 2
    new_img.paste(img, (paste_x, paste_y))
    
    return new_img

def generate_video_thumbnails(video_url: str) -> List:
    response = requests.get(video_url)
    video_path = f"/tmp/{uuid4()}.mp4"
    with open(video_path, 'wb') as f:
        f.write(response.content)
    
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    aspect_ratio = video_width / video_height
    thumbnails = []
    
    for i in range(4):
        cap.set(cv2.CAP_PROP_POS_FRAMES, (i * frame_count) // 4)
        ret, frame = cap.read()
        if ret:
            if aspect_ratio > 16/9:  # Wider than 16:9
                new_width = 640
                new_height = int(640 / aspect_ratio)
            else:  # Taller than 16:9
                new_height = 360
                new_width = int(360 * aspect_ratio)
            
            frame = cv2.resize(frame, (new_width, new_height))
            
            # Create a black canvas of 640x360
            canvas = np.zeros((360, 640, 3), dtype=np.uint8)
            
            # Calculate position to paste the resized frame
            y_offset = (360 - new_height) // 2
            x_offset = (640 - new_width) // 2
            
            # Paste the resized frame onto the canvas
            canvas[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = frame
            
            img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
            thumbnails.append(img)
    
    cap.release()
    os.remove(video_path)
    
    return thumbnails

def upload_thumbnails_to_storage(thumbnails: List, user_id: UUID, media_item_id: int) -> List[str]:
    thumbnail_urls = []
    for i, thumbnail in enumerate(thumbnails):
        buffer = BytesIO()
        thumbnail.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)
        
        file_key = f"user-{user_id}/thumbnails/{media_item_id}_{i}.png"
        upload_file_to_storage(buffer, file_key)
        
        thumbnail_url = f"{os.getenv('STORAGE_ENDPOINT_URL')}/{os.getenv('STORAGE_BUCKET')}/{file_key}"
        thumbnail_urls.append(thumbnail_url)
    
    return thumbnail_urls