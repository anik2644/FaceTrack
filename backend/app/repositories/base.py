"""Generic repository implementing common CRUD operations.

The Repository pattern isolates persistence concerns from business logic
(Single Responsibility) and lets services depend on a stable data-access
abstraction rather than on SQLAlchemy directly (Dependency Inversion).
"""
from __future__ import annotations

from typing import Generic, List, Optional, Sequence, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """CRUD building block parameterised by an ORM model type."""

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, obj_id: int) -> Optional[ModelType]:
        return self.db.get(self.model, obj_id)

    def list(self, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def all(self) -> List[ModelType]:
        return list(self.db.scalars(select(self.model)).all())

    def count(self) -> int:
        return int(self.db.scalar(select(func.count()).select_from(self.model)) or 0)

    def add(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelType) -> None:
        self.db.delete(obj)
        self.db.flush()

    def save(self) -> None:
        self.db.commit()

    def _scalars(self, stmt) -> Sequence[ModelType]:
        return self.db.scalars(stmt).all()
