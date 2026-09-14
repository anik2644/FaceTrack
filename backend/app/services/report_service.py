"""Reporting service: aggregates, trends and CSV export."""
from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import date
from typing import List

from sqlalchemy.orm import Session

from app.repositories.attendance_repository import AttendanceRepository
from app.schemas.attendance import DailyTrendPoint, ReportRow


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AttendanceRepository(db)

    def summary(
        self, start: date, end: date, *, department: str | None = None
    ) -> List[ReportRow]:
        records = self.repo.for_date_range(start, end, department=department)
        buckets: dict[int, dict] = defaultdict(
            lambda: {"present": set(), "late": set(), "conf": []}
        )
        meta: dict[int, dict] = {}
        for r in records:
            b = buckets[r.person_id]
            if r.status == "late":
                b["late"].add(r.event_date)
            else:
                b["present"].add(r.event_date)
            b["conf"].append(r.confidence)
            if r.person and r.person_id not in meta:
                meta[r.person_id] = {
                    "name": r.person.name,
                    "employee_id": r.person.employee_id,
                    "department": r.person.department,
                }

        rows: List[ReportRow] = []
        for pid, b in buckets.items():
            info = meta.get(pid, {"name": "Unknown", "employee_id": None, "department": None})
            avg_conf = sum(b["conf"]) / len(b["conf"]) if b["conf"] else 0.0
            rows.append(
                ReportRow(
                    person_id=pid,
                    name=info["name"],
                    employee_id=info["employee_id"],
                    department=info["department"],
                    days_present=len(b["present"]),
                    days_late=len(b["late"]),
                    avg_confidence=round(avg_conf, 3),
                )
            )
        rows.sort(key=lambda x: (-(x.days_present + x.days_late), x.name))
        return rows

    def daily_trend(self, start: date, end: date) -> List[DailyTrendPoint]:
        raw = self.repo.daily_trend(start, end)
        by_date: dict[date, dict[str, int]] = defaultdict(lambda: {"present": 0, "late": 0})
        for d, status, count in raw:
            by_date[d][status if status in ("present", "late") else "present"] += count
        return [
            DailyTrendPoint(event_date=d, present=v["present"], late=v["late"])
            for d, v in sorted(by_date.items())
        ]

    def export_csv(self, start: date, end: date, *, department: str | None = None) -> str:
        records = self.repo.for_date_range(start, end, department=department)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            ["Date", "Time", "Name", "Employee ID", "Department", "Status", "Confidence", "Camera"]
        )
        for r in records:
            person = r.person
            writer.writerow(
                [
                    r.event_date.isoformat(),
                    r.timestamp.strftime("%H:%M:%S"),
                    person.name if person else "Unknown",
                    person.employee_id if person else "",
                    person.department if person else "",
                    r.status,
                    f"{r.confidence:.3f}",
                    r.camera_name or "",
                ]
            )
        return buffer.getvalue()
