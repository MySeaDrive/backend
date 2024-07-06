from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from uuid import UUID

class User(SQLModel, table=True):
    __tablename__ = 'users'

    id: UUID = Field(default=None, primary_key=True)

class Dive(SQLModel, table=True):

    __tablename__ = 'dives'

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field()
    user_id: UUID = Field(foreign_key= 'users.id') # Diver

    media_items: List["MediaItem"] = Relationship(back_populates="dive")

class MediaItem(SQLModel, table=True):

    __tablename__ = 'media_items'

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: Optional[str] = None
    raw_url: str
    processed_url: Optional[str] = None
    mime_type: str
    user_id: UUID = Field(foreign_key= 'users.id') # Uploader
    dive_id: Optional[int] = Field(default= None, foreign_key='dives.id')
    thumbnails: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))

    dive: Optional[Dive] = Relationship(back_populates="media_items")

class NewDive(BaseModel):
    name: str

class UpdateDive(BaseModel):
    name: str

class NewMediaItem(BaseModel):
    filename: str
    pre_signed_url: str
    mime_type: str

class LoginData(BaseModel):
    email: str
    password: str

class UploadFileInfo(BaseModel):
    id: str
    name: str
    content_type: str
    size: int

class UploadUrlsRequest(BaseModel):
    files: List[UploadFileInfo]

class MediaItemResponse(BaseModel):
    id: int
    filename: Optional[str]
    raw_url: str
    processed_url: Optional[str]
    mime_type: str
    thumbnails: Optional[List[str]]

    model_config = ConfigDict(from_attributes=True)

class DiveResponse(BaseModel):
    id: int
    name: str
    user_id: UUID
    media_items: List[MediaItemResponse]

    model_config = ConfigDict(from_attributes=True)