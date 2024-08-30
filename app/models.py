from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from uuid import UUID
from enum import Enum
from datetime import datetime
from sqlalchemy import DateTime, func


class User(SQLModel, table=True):
    __tablename__ = 'users'

    id: UUID = Field(default=None, primary_key=True)

class Dive(SQLModel, table=True):

    __tablename__ = 'dives'

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field()
    user_id: UUID = Field(foreign_key= 'users.id') # Diver

    media_items: List["MediaItem"] = Relationship(back_populates="dive")
    log: Optional["Log"] = Relationship(back_populates="dive")

class MediaItemState(str, Enum):
    PROCESSING = "processing"
    READY = "ready"

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
    state: Optional[MediaItemState] = Field(default=None)
    created_at: datetime = Field(
        default_factory=func.now,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    is_favorite: bool = Field(default=False)

    dive: Optional[Dive] = Relationship(back_populates="media_items")

class Log(SQLModel, table=True):
    __tablename__ = 'logs'

    id: Optional[int] = Field(default=None, primary_key=True)
    dive_id: int = Field(foreign_key="dives.id", unique=True)
    starting_air: Optional[int] = Field(default=None)  # in bar
    ending_air: Optional[int] = Field(default=None)  # in bar
    dive_start_time: Optional[datetime] = Field(default=None)
    dive_duration: Optional[int] = Field(default=None)  # in minutes
    max_depth: Optional[float] = Field(default=None)  # in metres
    visibility: Optional[float] = Field(default=None)  # in metres
    water_temperature: Optional[float] = Field(default=None)  # in centigrade
    wetsuit_thickness: Optional[int] = Field(default=None)  # in mm
    wetsuit_type: Optional[str] = Field(default=None)
    weights: Optional[float] = Field(default=None)  # in kg
    fish_ids: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    notes: Optional[str] = Field(default=None)

    dive: Dive = Relationship(back_populates="log")
    
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
    state: MediaItemState
    created_at: datetime
    is_favorite: bool

    model_config = ConfigDict(from_attributes=True)

class DiveResponse(BaseModel):
    id: int
    name: str
    user_id: UUID
    media_items: List[MediaItemResponse]

    model_config = ConfigDict(from_attributes=True)

class LogCreate(BaseModel):
    starting_air: Optional[int] = None
    ending_air: Optional[int] = None
    dive_start_time: Optional[datetime] = None
    dive_duration: Optional[int] = None
    max_depth: Optional[float] = None
    visibility: Optional[float] = None
    water_temperature: Optional[float] = None
    wetsuit_thickness: Optional[int] = None
    wetsuit_type: Optional[str] = None
    weights: Optional[float] = None
    fish_ids: Optional[List[str]] = None
    notes: Optional[str] = None

class LogResponse(LogCreate):
    id: int
    dive_id: int

    model_config = ConfigDict(from_attributes=True)