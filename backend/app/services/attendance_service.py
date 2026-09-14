"""Attendance marking and querying service."""
from __future__ import annotations

from datetime import date, datetime, time as dtime
from typing import List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.attendance import Attendance
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.person_repository import PersonRepository
from app.schemas.attendance import AttendanceRead, AttendanceStats
from app.services.vision.types import FaceMatch

logger = get_logger(__name__)


def _parse_workday_start() -> dtime:
    hh, mm = settings.WORKDAY_START.split(":")
    return dtime(int(hh), int(mm))


class AttendanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AttendanceRepository(db)
        self.persons = PersonRepository(db)

    # ----- marking ---------------------------------------------------------
    def mark_from_match(self, match: FaceMatch, camera_name: str | None) -> Attendance | None:
        """Record attendance for a recognised person, honouring the cooldown.

        Returns the created record, or ``None`` if the person was already marked
        within the cooldown window.
        """
        if match.person_id is None:
            return None

        now = datetime.now()
        today = now.date()
        last = self.repo.last_for_person_on(match.person_id, today)
        if last is not None:
            elapsed = (now - last.timestamp).total_seconds()
            if elapsed < settings.ATTENDANCE_COOLDOWN_SECONDS:
                return None

        status = "present" if now.time() <= _parse_workday_start() else "late"
        record = Attendance(
            person_id=match.person_id,
            event_date=today,
            timestamp=now,
            confidence=round(match.confidence, 4),
            status=status,
            camera_name=camera_name or None,
        )
        record = self.repo.add(record)
        self.repo.save()
        logger.info("Attendance marked: %s (%s)", match.name, status)
        return record

    # ----- queries ---------------------------------------------------------
    def _to_read(self, record: Attendance) -> AttendanceRead:
        person = record.person
        return AttendanceRead(
            id=record.id,
            person_id=record.person_id,
            name=person.name if person else "Unknown",
            employee_id=person.employee_id if person else None,
            department=person.department if person else None,
            event_date=record.event_date,
            timestamp=record.timestamp,
            confidence=record.confidence,
            status=record.status,
            camera_name=record.camera_name,
            snapshot_path=record.snapshot_path,
        )

    def today(self) -> List[AttendanceRead]:
        return [self._to_read(r) for r in self.repo.for_day(date.today())]

    def range(
        self,
        start: date,
        end: date,
        *,
        person_id: int | None = None,
        department: str | None = None,
    ) -> List[AttendanceRead]:
        records = self.repo.for_date_range(
            start, end, person_id=person_id, department=department
        )
        return [self._to_read(r) for r in records]

    def stats(self) -> AttendanceStats:
        today = date.today()
        counts = self.repo.count_by_status_for_day(today)
        present = counts.get("present", 0)
        late = counts.get("late", 0)
        total_persons = self.persons.count()
        marked = present + late
        absent = max(0, total_persons - marked)
        rate = (marked / total_persons * 100) if total_persons else 0.0
        return AttendanceStats(
            total_persons=total_persons,
            present_today=present,
            late_today=late,
            absent_today=absent,
            attendance_rate=round(rate, 1),
            total_records=self.repo.count(),
        )
