from pydantic import BaseModel
from typing import Optional, Literal
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    __tablename__ = 'users'

    id: str = Field(default=None, primary_key=True)

class MediaItem(SQLModel, table=True):

    __tablename__ = 'media_items'

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: Optional[str] = None
    raw_url: str
    processed_url: Optional[str] = None
    mime_type: str # TODO Literal['image/jpeg','image/png','image/gif','image/bmp','image/webp','image/svg+xml','video/mp4','video/webm','video/ogg','video/x-msvideo','video/quicktime']
    user_id: str # Uploader
    dive_id: Optional[int] = None

class Dive(SQLModel, table=True):

    __tablename__ = 'dives'

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field()
    user_id: str # Diver

class NewDive(BaseModel):
    name: str

class LoginData(BaseModel):
    email: str
    password: str