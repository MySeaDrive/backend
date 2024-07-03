from fastapi import APIRouter, Depends, HTTPException, status
from ..models import Dive, NewDive, User, DiveResponse, MediaItem
from ..helpers.db import engine
from ..helpers.auth import get_current_user
from sqlmodel import Session, select
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
async def save_dive(new_dive: NewDive) -> Dive:

    with Session(engine) as session:
        dive = Dive(name=new_dive.name)
        session.add(dive)
        session.commit()
        session.refresh(dive)
        return dive
