"""Stream manager: the single owner of the live recognition session.

Implemented as a process-wide singleton because there is exactly one capture
device / recognition loop at a time. It ties together the capture thread, the
recognition pipeline, attendance marking and event broadcasting through
injected callbacks (keeping this class free of DB/WebSocket concerns).
"""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import Callable, Deque, Iterator, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.services.vision.pipeline import RecognitionPipeline
from app.services.vision.stream import VideoStream
from app.services.vision.types import FaceMatch

logger = get_logger(__name__)

# Callback invoked (in the worker thread) for every recognised known face.
DetectionCallback = Callable[[FaceMatch, str], None]


class StreamManager:
    _instance: Optional["StreamManager"] = None
    _singleton_lock = threading.Lock()

    def __new__(cls) -> "StreamManager":
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialised = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialised:  # avoid re-init on repeated construction
            return
        self.pipeline = RecognitionPipeline()
        self._stream: Optional[VideoStream] = None
        self._active = False
        self._camera_name: Optional[str] = None
        self._source: Optional[str] = None
        self._fps = 0.0
        self._detection_count = 0
        self._on_detection: Optional[DetectionCallback] = None
        self.recent_events: Deque[dict] = deque(maxlen=50)
        self._initialised = True

    # ----- wiring ----------------------------------------------------------
    def set_detection_callback(self, callback: DetectionCallback) -> None:
        self._on_detection = callback

    def load_gallery(self, entries) -> None:
        self.pipeline.gallery.load(entries)

    # ----- lifecycle -------------------------------------------------------
    def start(self, source: str | int, *, use_ffmpeg: bool, camera_name: str) -> bool:
        self.stop()
        stream = VideoStream(source, use_ffmpeg=use_ffmpeg)
        if not stream.open():
            return False
        self._stream = stream
        self._active = True
        self._camera_name = camera_name
        self._source = str(source)
        self._detection_count = 0
        logger.info("Recognition stream started (%s)", camera_name)
        return True

    def stop(self) -> None:
        self._active = False
        if self._stream is not None:
            self._stream.release()
            self._stream = None
        self._camera_name = None
        self._source = None
        self._fps = 0.0

    @property
    def is_active(self) -> bool:
        return self._active

    def status(self) -> dict:
        return {
            "active": self._active,
            "camera_name": self._camera_name,
            "source": self._source,
            "fps": round(self._fps, 1),
            "detections": self._detection_count,
            "known_faces": self.pipeline.gallery.size,
        }

    # ----- streaming -------------------------------------------------------
    def frames(self) -> Iterator[bytes]:
        """Yield annotated MJPEG frames while the stream is active."""
        from app.utils.image import encode_image_to_jpeg_bytes

        last_time = time.time()
        while self._active and self._stream is not None:
            frame = self._stream.read()
            if frame is None:
                time.sleep(0.01)
                continue

            result = self.pipeline.process(frame, annotate=True)
            for match in result.matches:
                if match.is_known and self._on_detection is not None:
                    self._detection_count += 1
                    try:
                        self._on_detection(match, self._camera_name or "")
                    except Exception as exc:  # noqa: BLE001
                        logger.error("Detection callback failed: %s", exc)

            # FPS (exponential moving average).
            now = time.time()
            instant = 1.0 / max(now - last_time, 1e-6)
            self._fps = 0.9 * self._fps + 0.1 * instant if self._fps else instant
            last_time = now

            from app.services.vision import drawing

            drawing.draw_hud(frame, self._fps, self.pipeline.gallery.size)
            payload = encode_image_to_jpeg_bytes(frame, settings.JPEG_QUALITY)
            if payload is None:
                continue
            yield (
                b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + payload + b"\r\n"
            )


def get_stream_manager() -> StreamManager:
    """Return the shared :class:`StreamManager` singleton."""
    return StreamManager()
