from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from ..models import Dive, NewDive, User, DiveResponse, UpdateDive, MediaItem, Log, LogCreate, LogResponse
from ..helpers.db import engine
from ..helpers.auth import get_current_user
from ..helpers.storage import delete_file_from_storage
from sqlmodel import Session, select, update, delete
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
async def delete_dive(
    id: int,
    delete_media: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user=Depends(get_current_user),
):
    with Session(engine) as session:
        # 1) verify the dive exists & belongs to this user
        dive = session.exec(
            select(Dive).where(Dive.id == id, Dive.user_id == current_user.id)
        ).first()
        if not dive:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dive not found"
            )

        # 2) delete or orphan any media items
        if delete_media:
            media_items = session.exec(
                select(MediaItem).where(MediaItem.dive_id == id)
            ).all()
            for mi in media_items:
                # schedule S3 deletes
                background_tasks.add_task(
                    delete_file_from_storage, mi.raw_url, current_user.id
                )
                if mi.processed_url and mi.processed_url != mi.raw_url:
                    background_tasks.add_task(
                        delete_file_from_storage, mi.processed_url, current_user.id
                    )
                session.delete(mi)
        else:
            session.exec(
                update(MediaItem)
                .where(MediaItem.dive_id == id)
                .values(dive_id=None)
            )

        # 3) core‐delete the dive row in one shot
        session.exec(
            delete(Dive)
            .where(Dive.id == id, Dive.user_id == current_user.id)
        )

        session.commit()

    return {"message": "Dive deleted successfully"}

    
@dives_router.get('/{dive_id}/log')
async def get_dive_log(dive_id: int, current_user: User = Depends(get_current_user)) -> LogResponse:
    with Session(engine) as session:
        query = select(Dive).where(Dive.id == dive_id, Dive.user_id == current_user.id)
        dive = session.exec(query).first()

        if not dive:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dive not found")
        
        log = session.exec(select(Log).where(Log.dive_id == dive_id)).first()
        
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found for this dive")
        
        return LogResponse.model_validate(log)
    
@dives_router.post('/{dive_id}/log')
async def create_or_update_dive_log(dive_id: int, log_data: LogCreate, current_user: User = Depends(get_current_user)) -> LogResponse:
    with Session(engine) as session:
        query = select(Dive).where(Dive.id == dive_id, Dive.user_id == current_user.id)
        dive = session.exec(query).first()

        if not dive:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dive not found")
        
        existing_log = session.exec(select(Log).where(Log.dive_id == dive_id)).first()

        if existing_log:

            for key, value in log_data.model_dump(exclude_unset=True).items():
                setattr(existing_log, key, value)
            log = existing_log

        else:
            log_data_dict = log_data.model_dump(exclude_unset=True)
            log = Log(dive_id=dive_id, **log_data_dict)
            session.add(log)
        
        session.commit()
        session.refresh(log)
        
        return LogResponse.model_validate(log)