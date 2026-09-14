"""Image encoding/decoding helpers shared across the app."""
from __future__ import annotations

import base64
import uuid
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from app.core.exceptions import ValidationError


def decode_base64_image(data_url: str) -> np.ndarray:
    """Decode a base64 data-URL (or raw base64) into a BGR OpenCV image."""
    if not data_url:
        raise ValidationError("No image data provided.")
    try:
        encoded = data_url.split(",", 1)[1] if "," in data_url else data_url
        image_bytes = base64.b64decode(encoded)
        buffer = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    except Exception as exc:  # pragma: no cover - defensive
        raise ValidationError("Could not decode image data.") from exc
    if image is None:
        raise ValidationError("Image data is not a valid image.")
    return image


def encode_image_to_base64(image: np.ndarray, quality: int = 85) -> str:
    """Encode a BGR image to a base64 JPEG data-URL."""
    ok, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise ValidationError("Failed to encode image.")
    b64 = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def encode_image_to_jpeg_bytes(image: np.ndarray, quality: int = 65) -> Optional[bytes]:
    """Encode a BGR image to raw JPEG bytes for MJPEG streaming."""
    ok, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buffer.tobytes() if ok else None


def save_image(image: np.ndarray, directory: Path, prefix: str = "img") -> str:
    """Persist an image to ``directory`` and return its path as a string."""
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{prefix}_{uuid.uuid4().hex[:12]}.jpg"
    path = directory / filename
    cv2.imwrite(str(path), image)
    return str(path)
