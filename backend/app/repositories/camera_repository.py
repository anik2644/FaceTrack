"""Camera data access."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.camera import Camera
from app.repositories.base import BaseRepository


class CameraRepository(BaseRepository[Camera]):
    def __init__(self, db: Session):
        super().__init__(Camera, db)

    def get_by_name(self, name: str) -> Optional[Camera]:
        return self.db.scalar(select(Camera).where(Camera.name == name))
