"""Camera management endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, get_camera_service
from app.schemas.camera import (
    CameraCreate,
    CameraRead,
    CameraTestRequest,
    CameraUpdate,
)
from app.schemas.common import Message
from app.services.camera_service import CameraService

router = APIRouter(prefix="/cameras", tags=["Cameras"])


@router.get("", response_model=list[CameraRead])
def list_cameras(
    _: CurrentUser, service: CameraService = Depends(get_camera_service)
) -> list[CameraRead]:
    return [CameraRead.model_validate(c) for c in service.list()]


@router.post("", response_model=CameraRead, status_code=201)
def create_camera(
    payload: CameraCreate,
    _: CurrentUser,
    service: CameraService = Depends(get_camera_service),
) -> CameraRead:
    return CameraRead.model_validate(service.create(payload))


@router.patch("/{camera_id}", response_model=CameraRead)
def update_camera(
    camera_id: int,
    payload: CameraUpdate,
    _: CurrentUser,
    service: CameraService = Depends(get_camera_service),
) -> CameraRead:
    return CameraRead.model_validate(service.update(camera_id, payload))


@router.delete("/{camera_id}", response_model=Message)
def delete_camera(
    camera_id: int,
    _: CurrentUser,
    service: CameraService = Depends(get_camera_service),
) -> Message:
    service.delete(camera_id)
    return Message(message="Camera deleted successfully.")


@router.post("/test", response_model=Message, summary="Test camera connectivity")
def test_camera(
    payload: CameraTestRequest,
    _: CurrentUser,
    service: CameraService = Depends(get_camera_service),
) -> Message:
    ok = service.test_connection(payload.source_type, payload.source)
    if ok:
        return Message(message="Connection successful.")
    return Message(success=False, message="Could not connect to the camera source.")
