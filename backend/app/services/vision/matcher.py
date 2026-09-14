"""Match face encodings against the gallery."""
from __future__ import annotations

import numpy as np

from app.core.config import settings
from app.services.vision.gallery import FaceGallery
from app.services.vision.types import BoundingBox, FaceMatch


class FaceMatcher:
    """Nearest-neighbour matcher using Euclidean distance on 128-d vectors."""

    def __init__(self, gallery: FaceGallery):
        self._gallery = gallery
        self._threshold = settings.FACE_RECOGNITION_THRESHOLD
        self._tolerance = settings.FACE_MATCH_TOLERANCE

    def match(self, encoding: np.ndarray, box: BoundingBox) -> FaceMatch:
        entries, matrix = self._gallery.snapshot()
        if matrix is None or not entries:
            return FaceMatch("Unknown", None, 0.0, box, is_known=False)

        # Vectorised Euclidean distance to every gallery encoding.
        distances = np.linalg.norm(matrix - encoding, axis=1)
        best_index = int(np.argmin(distances))
        best_distance = float(distances[best_index])
        confidence = max(0.0, 1.0 - best_distance)

        if best_distance <= self._tolerance and confidence >= self._threshold:
            entry = entries[best_index]
            return FaceMatch(
                name=entry.name,
                person_id=entry.person_id,
                confidence=confidence,
                box=box,
                is_known=True,
            )
        return FaceMatch("Unknown", None, confidence, box, is_known=False)
