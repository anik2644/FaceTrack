"""In-memory gallery of known face encodings.

Holds the encodings loaded from the database so the recognition loop never has
to hit the DB per frame. Thread-safe because it is read by the streaming worker
and refreshed from request threads.
"""
from __future__ import annotations

import threading
from typing import List

import numpy as np

from app.core.logging import get_logger
from app.services.vision.types import GalleryEntry

logger = get_logger(__name__)


class FaceGallery:
    def __init__(self) -> None:
        self._entries: List[GalleryEntry] = []
        self._matrix: np.ndarray | None = None
        self._lock = threading.RLock()

    def load(self, entries: List[GalleryEntry]) -> None:
        with self._lock:
            self._entries = entries
            self._matrix = (
                np.vstack([e.encoding for e in entries]) if entries else None
            )
        logger.info("Gallery loaded with %d encodings", len(entries))

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._entries)

    @property
    def is_empty(self) -> bool:
        return self.size == 0

    def snapshot(self) -> tuple[List[GalleryEntry], np.ndarray | None]:
        """Return a consistent (entries, matrix) pair for matching."""
        with self._lock:
            return list(self._entries), self._matrix
