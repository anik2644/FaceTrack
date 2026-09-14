"""Person schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PersonBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    employee_id: str | None = None
    department: str | None = None
    email: str | None = None
    phone: str | None = None
    is_active: bool = True


class PersonCreate(PersonBase):
    # Base64 data-URL captured from webcam or uploaded file.
    image: str = Field(description="Base64 data-URL of the enrollment photo.")


class PersonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    employee_id: str | None = None
    department: str | None = None
    email: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class AddEncodingRequest(BaseModel):
    image: str = Field(description="Base64 data-URL to add as an extra encoding.")


class PersonRead(PersonBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    photo_path: str | None = None
    encoding_count: int = 0
    created_at: datetime
