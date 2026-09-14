"""Aggregate router for API v1."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    attendance,
    auth,
    cameras,
    persons,
    recognition,
    reports,
    system,
)

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(persons.router)
api_router.include_router(attendance.router)
api_router.include_router(reports.router)
api_router.include_router(cameras.router)
api_router.include_router(recognition.router)
