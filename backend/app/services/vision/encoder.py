"""Face detection + encoding.

Wraps the optional ``face_recognition`` (dlib) library. The rest of the app
depends only on this small surface, so if dlib is unavailable the failure is
localised and reported cleanly instead of crashing the server.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import cv2
import numpy as np

from app.core.logging import get_logger
from app.services.vision.types import BoundingBox

logger = get_logger(__name__)

# NOTE: ``except BaseException`` is deliberate. The ``face_recognition`` package
# calls ``quit()`` (raising SystemExit, a BaseException) at import time when its
# model data is missing, which a plain ``except Exception`` would not catch.
try:  # pragma: no cover - optional heavy dependency
    import face_recognition

    _AVAILABLE = True
except BaseException as exc:  # noqa: BLE001
    face_recognition = None  # type: ignore
    _AVAILABLE = False
    logger.warning(
        "face_recognition unavailable (%s). Install it with: "
        "pip install face_recognition_models face-recognition",
        exc,
    )


class FaceEncoder:
    """Detects faces and produces 128-d embeddings."""

    @property
    def is_available(self) -> bool:
        return _AVAILABLE

    def encode_single(self, image_bgr: np.ndarray) -> Optional[np.ndarray]:
        """Return the encoding of the most prominent face, or ``None``."""
        if not _AVAILABLE:
            return None
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        if not locations:
            return None
        # Choose the largest face (area) as the subject.
        largest = max(locations, key=lambda loc: (loc[2] - loc[0]) * (loc[1] - loc[3]))
        encodings = face_recognition.face_encodings(rgb, [largest])
        return encodings[0] if encodings else None

    def detect_and_encode(
        self, image_bgr: np.ndarray, scale: float = 0.5
    ) -> List[Tuple[BoundingBox, np.ndarray]]:
        """Detect all faces in a frame and return (box, encoding) pairs.

        The frame is downscaled for the detection step (a big speed win) and the
        resulting boxes are scaled back to the original resolution.
        """
        if not _AVAILABLE:
            return []
        small = cv2.resize(image_bgr, (0, 0), fx=scale, fy=scale)
        rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb_small)
        if not locations:
            return []
        encodings = face_recognition.face_encodings(rgb_small, locations)

        results: List[Tuple[BoundingBox, np.ndarray]] = []
        inv = 1.0 / scale
        for (top, right, bottom, left), encoding in zip(locations, encodings):
            box = BoundingBox(
                x1=int(left * inv),
                y1=int(top * inv),
                x2=int(right * inv),
                y2=int(bottom * inv),
            )
            results.append((box, encoding))
        return results
