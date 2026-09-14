"""Shared/generic response schemas."""
from __future__ import annotations

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Message(BaseModel):
    success: bool = True
    message: str


class Page(BaseModel, Generic[T]):
    """Envelope for paginated list responses."""

    items: List[T]
    total: int
    page: int
    size: int
    pages: int


class HealthStatus(BaseModel):
    status: str
    app: str
    version: str
    environment: str
