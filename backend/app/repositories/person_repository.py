"""Person and face-encoding data access."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.person import FaceEncoding, Person
from app.repositories.base import BaseRepository


class PersonRepository(BaseRepository[Person]):
    def __init__(self, db: Session):
        super().__init__(Person, db)

    def get_by_name(self, name: str) -> Optional[Person]:
        return self.db.scalar(select(Person).where(Person.name == name))

    def search(
        self,
        *,
        query: str | None = None,
        department: str | None = None,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Person], int]:
        stmt = select(Person)
        count_stmt = select(func.count()).select_from(Person)

        conditions = []
        if query:
            like = f"%{query}%"
            conditions.append(
                or_(
                    Person.name.ilike(like),
                    Person.employee_id.ilike(like),
                    Person.email.ilike(like),
                )
            )
        if department:
            conditions.append(Person.department == department)
        if active_only:
            conditions.append(Person.is_active.is_(True))

        for cond in conditions:
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = int(self.db.scalar(count_stmt) or 0)
        stmt = stmt.order_by(Person.name).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all()), total

    def active_with_encodings(self) -> List[Person]:
        """Persons that are active and have at least one encoding."""
        stmt = (
            select(Person)
            .where(Person.is_active.is_(True))
            .where(Person.encodings.any())
        )
        return list(self.db.scalars(stmt).all())

    def add_encoding(self, person: Person, vector: bytes) -> FaceEncoding:
        encoding = FaceEncoding(person_id=person.id, vector=vector)
        self.db.add(encoding)
        self.db.flush()
        return encoding

    def departments(self) -> List[str]:
        stmt = (
            select(Person.department)
            .where(Person.department.is_not(None))
            .distinct()
            .order_by(Person.department)
        )
        return [d for d in self.db.scalars(stmt).all() if d]
