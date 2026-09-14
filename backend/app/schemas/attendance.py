"""Attendance and reporting schemas."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class AttendanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id: int
    name: str
    employee_id: str | None = None
    department: str | None = None
    event_date: date
    timestamp: datetime
    confidence: float
    status: str
    camera_name: str | None = None
    snapshot_path: str | None = None


class AttendanceStats(BaseModel):
    total_persons: int
    present_today: int
    late_today: int
    absent_today: int
    attendance_rate: float
    total_records: int


class ReportRow(BaseModel):
    person_id: int
    name: str
    employee_id: str | None = None
    department: str | None = None
    days_present: int
    days_late: int
    avg_confidence: float


class DailyTrendPoint(BaseModel):
    event_date: date
    present: int
    late: int
