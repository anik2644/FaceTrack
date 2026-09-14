"""Person (enrollment) endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, get_person_service
from app.schemas.common import Message, Page
from app.schemas.person import (
    AddEncodingRequest,
    PersonCreate,
    PersonRead,
    PersonUpdate,
)
from app.services.person_service import PersonService

router = APIRouter(prefix="/persons", tags=["Persons"])


@router.get("", response_model=Page[PersonRead], summary="List / search persons")
def list_persons(
    _: CurrentUser,
    service: PersonService = Depends(get_person_service),
    query: str | None = Query(default=None),
    department: str | None = Query(default=None),
    active_only: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> Page[PersonRead]:
    items, total = service.search(
        query=query,
        department=department,
        active_only=active_only,
        skip=(page - 1) * size,
        limit=size,
    )
    pages = (total + size - 1) // size if size else 1
    return Page(items=items, total=total, page=page, size=size, pages=pages)


@router.get("/departments", response_model=list[str], summary="Distinct departments")
def list_departments(
    _: CurrentUser, service: PersonService = Depends(get_person_service)
) -> list[str]:
    return service.departments()


@router.post("", response_model=PersonRead, status_code=201, summary="Enroll a person")
def create_person(
    payload: PersonCreate,
    _: CurrentUser,
    service: PersonService = Depends(get_person_service),
) -> PersonRead:
    return service.create(payload)


@router.get("/{person_id}", response_model=PersonRead)
def get_person(
    person_id: int,
    _: CurrentUser,
    service: PersonService = Depends(get_person_service),
) -> PersonRead:
    return service.get(person_id)


@router.patch("/{person_id}", response_model=PersonRead)
def update_person(
    person_id: int,
    payload: PersonUpdate,
    _: CurrentUser,
    service: PersonService = Depends(get_person_service),
) -> PersonRead:
    return service.update(person_id, payload)


@router.post("/{person_id}/encodings", response_model=PersonRead, summary="Add a face sample")
def add_encoding(
    person_id: int,
    payload: AddEncodingRequest,
    _: CurrentUser,
    service: PersonService = Depends(get_person_service),
) -> PersonRead:
    return service.add_encoding(person_id, payload.image)


@router.delete("/{person_id}", response_model=Message)
def delete_person(
    person_id: int,
    _: CurrentUser,
    service: PersonService = Depends(get_person_service),
) -> Message:
    service.delete(person_id)
    return Message(message="Person deleted successfully.")
