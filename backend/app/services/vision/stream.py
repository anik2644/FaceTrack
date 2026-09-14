"""Low-latency video capture with a background reader thread."""
from __future__ import annotations

import threading
import time
from typing import Optional

import cv2
import numpy as np

from app.core.logging import get_logger

logger = get_logger(__name__)


class VideoStream:
    """Continuously reads frames from a source into a single-slot buffer.

    Decoupling capture from processing keeps latency low: the processing loop
    always works on the freshest frame instead of draining a backlog.
    """

    def __init__(self, source: str | int, use_ffmpeg: bool = False):
        self._source = source
        self._use_ffmpeg = use_ffmpeg
        self._capture: Optional[cv2.VideoCapture] = None
        self._latest: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def open(self) -> bool:
        if self._use_ffmpeg:
            self._capture = cv2.VideoCapture(str(self._source), cv2.CAP_FFMPEG)
        else:
            self._capture = cv2.VideoCapture(self._source)
        self._capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not self._capture.isOpened():
            logger.error("Failed to open video source: %s", self._source)
            return False

        self._running = True
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()
        return True

    def _reader(self) -> None:
        while self._running and self._capture is not None:
            ok, frame = self._capture.read()
            if not ok:
                time.sleep(0.01)
                continue
            with self._lock:
                self._latest = frame

    def read(self) -> Optional[np.ndarray]:
        with self._lock:
            return None if self._latest is None else self._latest.copy()

    @property
    def is_running(self) -> bool:
        return self._running

    def release(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        with self._lock:
            self._latest = None
