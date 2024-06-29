from fastapi import APIRouter, Depends
from ..models import Dive, NewDive, User
from ..helpers.db import engine
from ..helpers.auth import get_current_user
from sqlmodel import Session, select

dives_router = APIRouter(prefix='/dives', tags=['Dives'])

@dives_router.get('/')
async def get_all_dives(current_user: User = Depends(get_current_user)) -> list[Dive]:

    with Session(engine) as session:
        query = select(Dive).where(Dive.user_id == current_user.id)
        dives = session.exec(query).all()
        return dives

@dives_router.get('/{id}')
async def get_dive(id: int) -> Dive | None:

    with Session(engine) as session:
        query = select(Dive).where(Dive.id == id)
        dive = session.exec(query).first()
        return dive


@dives_router.post('/save')
async def save_dive(new_dive: NewDive) -> Dive:

    with Session(engine) as session:
        dive = Dive(name=new_dive.name)
        session.add(dive)
        session.commit()
        session.refresh(dive)
        return dive
