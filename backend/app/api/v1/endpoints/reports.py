"""Reporting endpoints (summary, trends, CSV export)."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, get_report_service
from app.schemas.attendance import DailyTrendPoint, ReportRow
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/summary", response_model=list[ReportRow], summary="Per-person summary")
def summary(
    _: CurrentUser,
    service: ReportService = Depends(get_report_service),
    start_date: date = Query(...),
    end_date: date = Query(...),
    department: str | None = Query(default=None),
) -> list[ReportRow]:
    return service.summary(start_date, end_date, department=department)


@router.get("/trend", response_model=list[DailyTrendPoint], summary="Daily trend")
def trend(
    _: CurrentUser,
    service: ReportService = Depends(get_report_service),
    start_date: date = Query(...),
    end_date: date = Query(...),
) -> list[DailyTrendPoint]:
    return service.daily_trend(start_date, end_date)


@router.get("/export", summary="Export attendance as CSV")
def export_csv(
    _: CurrentUser,
    service: ReportService = Depends(get_report_service),
    start_date: date = Query(...),
    end_date: date = Query(...),
    department: str | None = Query(default=None),
) -> StreamingResponse:
    csv_data = service.export_csv(start_date, end_date, department=department)
    filename = f"attendance_{start_date}_{end_date}.csv"
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
