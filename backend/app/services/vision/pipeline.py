"""Recognition pipeline: orchestrates detection, encoding and matching.

This class is the Facade over the individual vision components. It composes
them (Composition over inheritance) and applies frame-skipping so heavy work
runs only every Nth frame while the stream stays smooth.
"""
from __future__ import annotations

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.services.vision import drawing
from app.services.vision.detector import PersonDetector, YoloPersonDetector
from app.services.vision.encoder import FaceEncoder
from app.services.vision.gallery import FaceGallery
from app.services.vision.matcher import FaceMatcher
from app.services.vision.types import BoundingBox, FaceMatch, FrameResult

logger = get_logger(__name__)


class RecognitionPipeline:
    def __init__(
        self,
        detector: PersonDetector | None = None,
        encoder: FaceEncoder | None = None,
        gallery: FaceGallery | None = None,
    ):
        self.gallery = gallery or FaceGallery()
        self.detector = detector or YoloPersonDetector()
        self.encoder = encoder or FaceEncoder()
        self.matcher = FaceMatcher(self.gallery)
        self._frame_index = 0
        self._last_result = FrameResult()

    # ----- capability introspection ---------------------------------------
    @property
    def detector_ready(self) -> bool:
        return self.detector.is_ready

    @property
    def encoder_ready(self) -> bool:
        return self.encoder.is_available

    # ----- processing ------------------------------------------------------
    def process(self, frame: np.ndarray, *, annotate: bool = True) -> FrameResult:
        """Process a frame, returning matches. Applies frame-skipping."""
        self._frame_index += 1
        if self._frame_index % settings.FRAME_SKIP != 0:
            # Re-draw the last known result so boxes don't flicker.
            if annotate:
                for match in self._last_result.matches:
                    drawing.draw_match(frame, match)
            return FrameResult()

        matches = self._recognise(frame)
        self._last_result = FrameResult(matches=matches)

        if annotate:
            for match in matches:
                drawing.draw_match(frame, match)
        return self._last_result

    def _recognise(self, frame: np.ndarray) -> list[FaceMatch]:
        matches: list[FaceMatch] = []

        # Prefer person-region cropping via YOLO; fall back to whole-frame face
        # detection when the detector is unavailable.
        regions: list[tuple[np.ndarray, int, int]] = []
        if self.detector.is_ready:
            for det in self.detector.detect(frame):
                x1, y1, x2, y2 = det.box.as_tuple()
                crop = frame[max(0, y1):y2, max(0, x1):x2]
                if crop.size:
                    regions.append((crop, max(0, x1), max(0, y1)))
        else:
            regions.append((frame, 0, 0))

        for crop, offset_x, offset_y in regions:
            for box, encoding in self.encoder.detect_and_encode(crop):
                # Translate crop-local box back to full-frame coordinates.
                global_box = BoundingBox(
                    box.x1 + offset_x,
                    box.y1 + offset_y,
                    box.x2 + offset_x,
                    box.y2 + offset_y,
                )
                matches.append(self.matcher.match(encoding, global_box))
        return matches
