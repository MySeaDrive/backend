import os
from ..models import MediaItem
from ..helpers.db import engine
from sqlmodel import Session

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