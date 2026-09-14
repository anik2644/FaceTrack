"""Camera schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CameraBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    source_type: str = Field(default="webcam", pattern="^(webcam|rtsp|http)$")
    source: str
    location: str | None = None
    is_active: bool = True


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    name: str | None = None
    source_type: str | None = Field(default=None, pattern="^(webcam|rtsp|http)$")
    source: str | None = None
    location: str | None = None
    is_active: bool | None = None


class CameraRead(CameraBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class CameraTestRequest(BaseModel):
    source_type: str = Field(default="webcam", pattern="^(webcam|rtsp|http)$")
    source: str


class StreamStartRequest(BaseModel):
    camera_id: int | None = None
    # Ad-hoc source when no saved camera is used.
    source_type: str = Field(default="webcam", pattern="^(webcam|rtsp|http)$")
    source: str = "0"
    camera_name: str | None = None
