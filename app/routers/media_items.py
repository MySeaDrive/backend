from fastapi import APIRouter, UploadFile, BackgroundTasks
from tempfile import NamedTemporaryFile
from ..helpers.storage import copy_to_storage
from ..models import MediaItem
from ..helpers.db import engine
from sqlmodel import Session, select

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
