"""Person enrollment and management service."""
from __future__ import annotations

import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, VisionError
from app.core.logging import get_logger
from app.models.person import Person
from app.repositories.person_repository import PersonRepository
from app.schemas.person import PersonCreate, PersonRead, PersonUpdate
from app.services.vision.encoder import FaceEncoder
from app.services.vision.types import GalleryEntry
from app.utils.image import decode_base64_image, save_image

logger = get_logger(__name__)


def encoding_to_bytes(vector: np.ndarray) -> bytes:
    return np.asarray(vector, dtype=np.float64).tobytes()


def bytes_to_encoding(raw: bytes) -> np.ndarray:
    return np.frombuffer(raw, dtype=np.float64)


class PersonService:
    """Encapsulates all business rules around enrolled persons."""

    def __init__(self, db: Session, encoder: FaceEncoder | None = None):
        self.db = db
        self.repo = PersonRepository(db)
        self.encoder = encoder or FaceEncoder()

    # ----- helpers ---------------------------------------------------------
    @staticmethod
    def to_read(person: Person) -> PersonRead:
        data = PersonRead.model_validate(person)
        data.encoding_count = len(person.encodings)
        return data

    def _encode_or_raise(self, image_data_url: str) -> tuple[np.ndarray, "np.ndarray"]:
        if not self.encoder.is_available:
            raise VisionError(
                "Face recognition engine is not available on the server."
            )
        image = decode_base64_image(image_data_url)
        encoding = self.encoder.encode_single(image)
        if encoding is None:
            raise VisionError(
                "No face detected. Ensure the face is clear and well-lit."
            )
        return image, encoding

    # ----- CRUD ------------------------------------------------------------
    def create(self, payload: PersonCreate) -> PersonRead:
        if self.repo.get_by_name(payload.name):
            raise ConflictError(f"A person named '{payload.name}' already exists.")

        image, encoding = self._encode_or_raise(payload.image)
        photo_path = save_image(image, settings.FACES_DIR, prefix="face")

        person = Person(
            name=payload.name,
            employee_id=payload.employee_id,
            department=payload.department,
            email=payload.email,
            phone=payload.phone,
            is_active=payload.is_active,
            photo_path=photo_path,
        )
        person = self.repo.add(person)
        self.repo.add_encoding(person, encoding_to_bytes(encoding))
        self.repo.save()
        self.db.refresh(person)
        logger.info("Registered person '%s' (id=%s)", person.name, person.id)
        return self.to_read(person)

    def add_encoding(self, person_id: int, image_data_url: str) -> PersonRead:
        person = self._get_or_raise(person_id)
        _, encoding = self._encode_or_raise(image_data_url)
        self.repo.add_encoding(person, encoding_to_bytes(encoding))
        self.repo.save()
        self.db.refresh(person)
        return self.to_read(person)

    def update(self, person_id: int, payload: PersonUpdate) -> PersonRead:
        person = self._get_or_raise(person_id)
        updates = payload.model_dump(exclude_unset=True)
        if "name" in updates and updates["name"] != person.name:
            if self.repo.get_by_name(updates["name"]):
                raise ConflictError("Another person already uses that name.")
        for field, value in updates.items():
            setattr(person, field, value)
        self.repo.save()
        self.db.refresh(person)
        return self.to_read(person)

    def delete(self, person_id: int) -> None:
        person = self._get_or_raise(person_id)
        self.repo.delete(person)
        self.repo.save()

    def get(self, person_id: int) -> PersonRead:
        return self.to_read(self._get_or_raise(person_id))

    def search(self, **kwargs) -> tuple[list[PersonRead], int]:
        persons, total = self.repo.search(**kwargs)
        return [self.to_read(p) for p in persons], total

    def departments(self) -> list[str]:
        return self.repo.departments()

    # ----- gallery ---------------------------------------------------------
    def build_gallery(self) -> list[GalleryEntry]:
        """Materialise gallery entries for the recognition pipeline."""
        entries: list[GalleryEntry] = []
        for person in self.repo.active_with_encodings():
            for enc in person.encodings:
                entries.append(
                    GalleryEntry(
                        person_id=person.id,
                        name=person.name,
                        department=person.department,
                        encoding=bytes_to_encoding(enc.vector),
                    )
                )
        return entries

    def _get_or_raise(self, person_id: int) -> Person:
        person = self.repo.get(person_id)
        if not person:
            raise NotFoundError(f"Person {person_id} not found.")
        return person
