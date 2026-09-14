"""Person detection strategies.

An abstract :class:`PersonDetector` defines the contract (Interface
Segregation / Dependency Inversion); :class:`YoloPersonDetector` is the default
implementation. New detectors (e.g. a lightweight HOG detector) can be dropped
in without touching the pipeline.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.services.vision.types import BoundingBox, PersonDetection

logger = get_logger(__name__)


class PersonDetector(ABC):
    """Contract for anything that can locate people in a frame."""

    @abstractmethod
    def detect(self, frame: np.ndarray) -> List[PersonDetection]:
        ...

    @property
    @abstractmethod
    def is_ready(self) -> bool:
        ...


class YoloPersonDetector(PersonDetector):
    """YOLOv8 person detector (COCO class 0)."""

    PERSON_CLASS_ID = 0

    def __init__(self, model_path: str | None = None, confidence: float | None = None):
        self._confidence = confidence or settings.YOLO_CONFIDENCE
        self._model = None
        model_path = model_path or settings.YOLO_MODEL_PATH
        try:
            from ultralytics import YOLO

            self._model = YOLO(model_path)
            logger.info("YOLO model loaded from %s", model_path)
        except Exception as exc:  # pragma: no cover - heavy dependency
            logger.warning("Could not load YOLO model (%s): %s", model_path, exc)
            self._model = None

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    def detect(self, frame: np.ndarray) -> List[PersonDetection]:
        if self._model is None:
            return []
        detections: List[PersonDetection] = []
        results = self._model(frame, verbose=False, conf=self._confidence)
        for result in results:
            for box in result.boxes:
                if int(box.cls) != self.PERSON_CLASS_ID:
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detections.append(
                    PersonDetection(
                        box=BoundingBox(x1, y1, x2, y2),
                        confidence=float(box.conf[0]),
                    )
                )
        return detections
