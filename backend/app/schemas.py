from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserOut(BaseModel):
    id: UUID
    email: str
    display_name: str
    avatar_url: str | None

    model_config = {"from_attributes": True}


class TagOut(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class TagWithCount(BaseModel):
    name: str
    count: int


class SoundOut(BaseModel):
    id: UUID
    filename: str
    duration_seconds: float | None
    notes: str | None
    is_new: bool
    ai_tagged: bool
    mime_type: str
    tags: list[TagOut]
    is_favorited: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SoundListResponse(BaseModel):
    items: list[SoundOut]
    total: int
    page: int
    per_page: int


class AddTagRequest(BaseModel):
    tag: str


class UpdateSoundRequest(BaseModel):
    notes: str | None = None
    is_new: bool | None = None
    ai_tagged: bool | None = None
    duration_seconds: float | None = None
