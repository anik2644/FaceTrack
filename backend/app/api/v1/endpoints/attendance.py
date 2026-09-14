"""Attendance endpoints."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, get_attendance_service
from app.schemas.attendance import AttendanceRead, AttendanceStats
from app.services.attendance_service import AttendanceService

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("/today", response_model=list[AttendanceRead], summary="Today's attendance")
def today(
    _: CurrentUser, service: AttendanceService = Depends(get_attendance_service)
) -> list[AttendanceRead]:
    return service.today()


@router.get("/stats", response_model=AttendanceStats, summary="Dashboard statistics")
def stats(
    _: CurrentUser, service: AttendanceService = Depends(get_attendance_service)
) -> AttendanceStats:
    return service.stats()


@router.get("", response_model=list[AttendanceRead], summary="Query attendance by range")
def query(
    _: CurrentUser,
    service: AttendanceService = Depends(get_attendance_service),
    start_date: date = Query(...),
    end_date: date = Query(...),
    person_id: int | None = Query(default=None),
    department: str | None = Query(default=None),
) -> list[AttendanceRead]:
    return service.range(
        start_date, end_date, person_id=person_id, department=department
    )
