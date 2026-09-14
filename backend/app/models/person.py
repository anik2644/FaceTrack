"""Person (enrolled subject) and their face encodings."""
from __future__ import annotations

from typing import List

from sqlalchemy import Boolean, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PKMixin, TimestampMixin


class Person(Base, PKMixin, TimestampMixin):
    __tablename__ = "persons"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    employee_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    photo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    encodings: Mapped[List["FaceEncoding"]] = relationship(
        back_populates="person",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    attendance_records: Mapped[List["Attendance"]] = relationship(  # noqa: F821
        back_populates="person",
        cascade="all, delete-orphan",
    )


class FaceEncoding(Base, PKMixin, TimestampMixin):
    """A single 128-d face embedding for a person.

    Storing multiple encodings per person (different angles/lighting) markedly
    improves recognition robustness compared to a single reference vector.
    """

    __tablename__ = "face_encodings"

    person_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # numpy float64[128] serialised with numpy.tobytes().
    vector: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    person: Mapped["Person"] = relationship(back_populates="encodings")
