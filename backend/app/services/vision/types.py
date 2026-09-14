"""Value objects shared across the vision pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

import numpy as np


@dataclass
class BoundingBox:
    x1: int
    y1: int
    x2: int
    y2: int

    def as_tuple(self) -> Tuple[int, int, int, int]:
        return self.x1, self.y1, self.x2, self.y2


@dataclass
class PersonDetection:
    """A person detected by the object detector."""

    box: BoundingBox
    confidence: float


@dataclass
class FaceMatch:
    """Result of matching a detected face against the gallery."""

    name: str
    person_id: Optional[int]
    confidence: float
    box: BoundingBox
    is_known: bool = False


@dataclass
class FrameResult:
    """Everything produced from processing a single frame."""

    matches: list[FaceMatch] = field(default_factory=list)


@dataclass
class GalleryEntry:
    person_id: int
    name: str
    department: Optional[str]
    encoding: np.ndarray
