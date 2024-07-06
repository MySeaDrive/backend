from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from ..models import Dive, NewDive, User, DiveResponse, UpdateDive, MediaItem
from ..helpers.db import engine
from ..helpers.auth import get_current_user
from ..helpers.storage import delete_file_from_storage
from sqlmodel import Session, select, update
from typing import List

dives_router = APIRouter(prefix='/dives', tags=['Dives'])

@dives_router.get('/')
async def get_all_dives(current_user: User = Depends(get_current_user)) -> List[DiveResponse]:

    with Session(engine) as session:
        query = select(Dive).where(Dive.user_id == current_user.id)
        dives = session.exec(query).all()
        return [DiveResponse.model_validate(dive) for dive in dives]

@dives_router.get('/{id}')
async def get_dive(id: int, current_user: User = Depends(get_current_user)) -> DiveResponse:

    with Session(engine) as session:
        query = select(Dive).where(Dive.id == id, Dive.user_id == current_user.id)
        
        dive = session.exec(query).first()
        if not dive:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dive not found")
        
        return DiveResponse.model_validate(dive)


@dives_router.post('/save')
async def save_dive(new_dive: NewDive, current_user: User = Depends(get_current_user)) -> Dive:

    with Session(engine) as session:
        dive = Dive(name = new_dive.name, user_id = current_user.id)
        session.add(dive)
        session.commit()
        session.refresh(dive)
        return dive

@dives_router.patch('/{id}')
async def update_dive(id: int, update_data: UpdateDive, current_user: User = Depends(get_current_user)) -> DiveResponse:
    with Session(engine) as session:
        query = select(Dive).where(Dive.id == id, Dive.user_id == current_user.id)
        dive = session.exec(query).first()
        
        if not dive:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dive not found")
        
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(dive, field, value)
        
        session.add(dive)
        session.commit()
        session.refresh(dive)
        
        return DiveResponse.model_validate(dive)
    
@dives_router.delete('/{id}')
async def delete_dive(id: int, delete_media: bool = False, background_tasks: BackgroundTasks = BackgroundTasks(), current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        query = select(Dive).where(Dive.id == id, Dive.user_id == current_user.id)
        dive = session.exec(query).first()
        
        if not dive:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dive not found")
        
        if delete_media:
            media_items = session.exec(select(MediaItem).where(MediaItem.dive_id == id)).all()
            for media_item in media_items:
                background_tasks.add_task(delete_file_from_storage, media_item.raw_url, current_user.id)
                if media_item.processed_url and media_item.processed_url != media_item.raw_url:
                    background_tasks.add_task(delete_file_from_storage, media_item.processed_url, current_user.id)
                session.delete(media_item)
        else:
            # If not deleting media, just set dive_id to None for associated media items
            session.exec(update(MediaItem).where(MediaItem.dive_id == id).values(dive_id=None))
        
        session.delete(dive)
        session.commit()
        
        return {"message": "Dive deleted successfully"}