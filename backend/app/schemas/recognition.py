"""Recognition/streaming runtime schemas."""
from __future__ import annotations

from pydantic import BaseModel


class DetectionEvent(BaseModel):
    """A single recognised detection broadcast over WebSocket."""

    name: str
    person_id: int | None = None
    confidence: float
    department: str | None = None
    status: str
    timestamp: str
    marked: bool = False


class StreamStatus(BaseModel):
    active: bool
    camera_name: str | None = None
    source: str | None = None
    fps: float = 0.0
    detections: int = 0
    known_faces: int = 0


class ModelStatus(BaseModel):
    yolo_loaded: bool
    face_recognition_available: bool
    known_faces: int
    yolo_model_path: str
