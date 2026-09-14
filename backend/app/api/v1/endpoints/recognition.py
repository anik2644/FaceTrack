"""Live recognition: stream control, MJPEG feed, snapshots and events."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, DbSession
from app.api.websocket import connection_manager
from app.core.exceptions import NotFoundError, VisionError
from app.core.logging import get_logger
from app.schemas.camera import CameraTestRequest, StreamStartRequest
from app.schemas.common import Message
from app.schemas.recognition import StreamStatus
from app.services.attendance_service import AttendanceService
from app.services.camera_service import CameraService
from app.services.person_service import PersonService
from app.services.vision.manager import get_stream_manager
from app.services.vision.types import FaceMatch
from app.db.session import session_scope
from app.utils.image import encode_image_to_base64

logger = get_logger(__name__)
router = APIRouter(prefix="/recognition", tags=["Recognition"])


def _make_detection_callback():
    """Build the worker-thread callback that marks attendance and broadcasts.

    It runs outside the request lifecycle, so it opens its own DB session.
    """

    def _callback(match: FaceMatch, camera_name: str) -> None:
        with session_scope() as db:
            record = AttendanceService(db).mark_from_match(match, camera_name)
            marked = record is not None
        event = {
            "name": match.name,
            "person_id": match.person_id,
            "confidence": round(match.confidence, 3),
            "status": record.status if record else "seen",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "marked": marked,
        }
        manager = get_stream_manager()
        manager.recent_events.appendleft(event)
        connection_manager.publish_threadsafe(event)

    return _callback


@router.post("/start", response_model=StreamStatus, summary="Start live recognition")
def start_stream(
    payload: StreamStartRequest, db: DbSession, _: CurrentUser
) -> StreamStatus:
    camera_service = CameraService(db)

    if payload.camera_id is not None:
        camera = camera_service.get(payload.camera_id)
        source_type, source, name = camera.source_type, camera.source, camera.name
    else:
        source_type, source = payload.source_type, payload.source
        name = payload.camera_name or "Ad-hoc camera"

    opencv_source, use_ffmpeg = CameraService.resolve_source(source_type, source)

    manager = get_stream_manager()
    # Refresh the gallery from the DB before starting.
    manager.load_gallery(PersonService(db).build_gallery())
    manager.set_detection_callback(_make_detection_callback())

    if not manager.start(opencv_source, use_ffmpeg=use_ffmpeg, camera_name=name):
        raise VisionError("Could not open the camera / stream source.")
    return StreamStatus(**manager.status())


@router.post("/stop", response_model=Message, summary="Stop live recognition")
def stop_stream(_: CurrentUser) -> Message:
    get_stream_manager().stop()
    return Message(message="Recognition stream stopped.")


@router.get("/status", response_model=StreamStatus, summary="Stream status")
def stream_status(_: CurrentUser) -> StreamStatus:
    return StreamStatus(**get_stream_manager().status())


@router.get("/feed", summary="MJPEG video feed (annotated)")
def video_feed() -> StreamingResponse:
    manager = get_stream_manager()
    if not manager.is_active:
        raise NotFoundError("No active recognition stream.")
    return StreamingResponse(
        manager.frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.post("/snapshot", summary="Grab a single frame from a source")
def snapshot(payload: CameraTestRequest, db: DbSession, _: CurrentUser) -> dict:
    """Capture one frame from a source for enrollment previews."""
    import cv2

    opencv_source, use_ffmpeg = CameraService.resolve_source(
        payload.source_type, payload.source
    )
    cap = (
        cv2.VideoCapture(opencv_source, cv2.CAP_FFMPEG)
        if use_ffmpeg
        else cv2.VideoCapture(opencv_source)
    )
    try:
        if not cap.isOpened():
            raise VisionError("Could not connect to the source.")
        frame = None
        for _ in range(5):  # let the stream stabilise
            ok, f = cap.read()
            if ok:
                frame = f
        if frame is None:
            raise VisionError("Could not read a frame from the source.")
        return {"success": True, "image": encode_image_to_base64(frame, quality=85)}
    finally:
        cap.release()


@router.get("/events", summary="Recent detection events (fallback for polling)")
def recent_events(_: CurrentUser) -> list[dict]:
    return list(get_stream_manager().recent_events)


@router.websocket("/ws")
async def recognition_ws(websocket: WebSocket) -> None:
    """Push live detection events to the frontend."""
    await connection_manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive; we only push server -> client.
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
