"""Attendance event model."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PKMixin


class Attendance(Base, PKMixin):
    __tablename__ = "attendance"

    person_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), index=True, nullable=False
    )
    event_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    # "present" | "late" — computed against the configured workday start.
    status: Mapped[str] = mapped_column(String(16), default="present", nullable=False)
    camera_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    snapshot_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    person: Mapped["Person"] = relationship(back_populates="attendance_records")  # noqa: F821
