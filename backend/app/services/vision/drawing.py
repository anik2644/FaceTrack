"""Overlay drawing helpers for annotated video frames."""
from __future__ import annotations

import cv2
import numpy as np

from app.services.vision.types import FaceMatch

_KNOWN_COLOR = (0, 200, 0)
_UNKNOWN_COLOR = (0, 0, 255)
_FONT = cv2.FONT_HERSHEY_SIMPLEX


def draw_match(frame: np.ndarray, match: FaceMatch) -> None:
    """Draw a labelled bounding box for a single face match."""
    x1, y1, x2, y2 = match.box.as_tuple()
    color = _KNOWN_COLOR if match.is_known else _UNKNOWN_COLOR
    label = (
        f"{match.name} {match.confidence * 100:.0f}%" if match.is_known else "Unknown"
    )

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    (tw, th), _ = cv2.getTextSize(label, _FONT, 0.6, 2)
    cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 8, y1), color, -1)
    cv2.putText(frame, label, (x1 + 4, y1 - 6), _FONT, 0.6, (255, 255, 255), 2)


def draw_hud(frame: np.ndarray, fps: float, known: int) -> None:
    """Draw a lightweight heads-up display in the corner."""
    text = f"FPS: {fps:4.1f}  |  Gallery: {known}"
    cv2.rectangle(frame, (0, 0), (260, 28), (0, 0, 0), -1)
    cv2.putText(frame, text, (8, 19), _FONT, 0.5, (0, 255, 180), 1)
