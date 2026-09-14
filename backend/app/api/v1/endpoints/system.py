"""System / diagnostics endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import HealthStatus
from app.schemas.recognition import ModelStatus
from app.services.vision.manager import get_stream_manager

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthStatus, summary="Health check")
def health() -> HealthStatus:
    return HealthStatus(
        status="ok",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )


@router.get("/model-status", response_model=ModelStatus, summary="ML model status")
def model_status() -> ModelStatus:
    pipeline = get_stream_manager().pipeline
    return ModelStatus(
        yolo_loaded=pipeline.detector_ready,
        face_recognition_available=pipeline.encoder_ready,
        known_faces=pipeline.gallery.size,
        yolo_model_path=settings.YOLO_MODEL_PATH,
    )
