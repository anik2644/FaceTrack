"""Attendance data access and aggregation queries."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.attendance import Attendance
from app.models.person import Person
from app.repositories.base import BaseRepository


class AttendanceRepository(BaseRepository[Attendance]):
    def __init__(self, db: Session):
        super().__init__(Attendance, db)

    def last_for_person_on(self, person_id: int, day: date) -> Optional[Attendance]:
        stmt = (
            select(Attendance)
            .where(Attendance.person_id == person_id, Attendance.event_date == day)
            .order_by(Attendance.timestamp.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def for_date_range(
        self,
        start: date,
        end: date,
        *,
        person_id: int | None = None,
        department: str | None = None,
    ) -> List[Attendance]:
        stmt = (
            select(Attendance)
            .options(joinedload(Attendance.person))
            .join(Person)
            .where(Attendance.event_date >= start, Attendance.event_date <= end)
            .order_by(Attendance.timestamp.desc())
        )
        if person_id:
            stmt = stmt.where(Attendance.person_id == person_id)
        if department:
            stmt = stmt.where(Person.department == department)
        return list(self.db.scalars(stmt).all())

    def for_day(self, day: date) -> List[Attendance]:
        return self.for_date_range(day, day)

    def count_by_status_for_day(self, day: date) -> dict[str, int]:
        stmt = (
            select(Attendance.status, func.count())
            .where(Attendance.event_date == day)
            .group_by(Attendance.status)
        )
        return {status: int(count) for status, count in self.db.execute(stmt).all()}

    def daily_trend(self, start: date, end: date) -> list[tuple[date, str, int]]:
        stmt = (
            select(Attendance.event_date, Attendance.status, func.count())
            .where(Attendance.event_date >= start, Attendance.event_date <= end)
            .group_by(Attendance.event_date, Attendance.status)
            .order_by(Attendance.event_date)
        )
        return [(d, s, int(c)) for d, s, c in self.db.execute(stmt).all()]
