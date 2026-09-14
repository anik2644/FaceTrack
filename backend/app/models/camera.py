"""CCTV / webcam source configuration model."""
from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PKMixin, TimestampMixin


class Camera(Base, PKMixin, TimestampMixin):
    __tablename__ = "cameras"

    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    # "webcam" | "rtsp" | "http"
    source_type: Mapped[str] = mapped_column(String(16), default="webcam", nullable=False)
    # Device index (webcam) or stream URL (rtsp/http), stored as text.
    source: Mapped[str] = mapped_column(String(512), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
