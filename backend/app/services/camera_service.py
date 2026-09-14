"""Camera management and connectivity testing."""
from __future__ import annotations

import cv2
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.camera import Camera
from app.repositories.camera_repository import CameraRepository
from app.schemas.camera import CameraCreate, CameraUpdate


class CameraService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CameraRepository(db)

    def create(self, payload: CameraCreate) -> Camera:
        if self.repo.get_by_name(payload.name):
            raise ConflictError("A camera with that name already exists.")
        camera = Camera(**payload.model_dump())
        camera = self.repo.add(camera)
        self.repo.save()
        return camera

    def update(self, camera_id: int, payload: CameraUpdate) -> Camera:
        camera = self._get_or_raise(camera_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(camera, field, value)
        self.repo.save()
        self.db.refresh(camera)
        return camera

    def delete(self, camera_id: int) -> None:
        camera = self._get_or_raise(camera_id)
        self.repo.delete(camera)
        self.repo.save()

    def get(self, camera_id: int) -> Camera:
        return self._get_or_raise(camera_id)

    def list(self) -> list[Camera]:
        return self.repo.all()

    @staticmethod
    def resolve_source(source_type: str, source: str) -> tuple[str | int, bool]:
        """Return (opencv_source, use_ffmpeg) for a camera definition."""
        if source_type == "webcam":
            try:
                return int(source), False
            except ValueError:
                return 0, False
        return source, True  # rtsp / http via FFMPEG backend

    def test_connection(self, source_type: str, source: str) -> bool:
        opencv_source, use_ffmpeg = self.resolve_source(source_type, source)
        cap = (
            cv2.VideoCapture(opencv_source, cv2.CAP_FFMPEG)
            if use_ffmpeg
            else cv2.VideoCapture(opencv_source)
        )
        try:
            if not cap.isOpened():
                return False
            ok, _ = cap.read()
            return bool(ok)
        finally:
            cap.release()

    def _get_or_raise(self, camera_id: int) -> Camera:
        camera = self.repo.get(camera_id)
        if not camera:
            raise NotFoundError(f"Camera {camera_id} not found.")
        return camera
