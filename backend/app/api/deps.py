"""Shared FastAPI dependencies (DB session, current user, service factories)."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.attendance_service import AttendanceService
from app.services.camera_service import CameraService
from app.services.person_service import PersonService
from app.services.report_service import ReportService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/token", auto_error=False
)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession, token: Annotated[str | None, Depends(oauth2_scheme)]
) -> User:
    if not token:
        raise AuthenticationError("Not authenticated.")
    payload = decode_access_token(token)
    username = payload.get("sub")
    if not username:
        raise AuthenticationError("Invalid token payload.")
    user = UserRepository(db).get_by_username(username)
    if not user or not user.is_active:
        raise AuthenticationError("User no longer exists or is inactive.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


# ----- service providers ---------------------------------------------------
def get_person_service(db: DbSession) -> PersonService:
    return PersonService(db)


def get_attendance_service(db: DbSession) -> AttendanceService:
    return AttendanceService(db)


def get_report_service(db: DbSession) -> ReportService:
    return ReportService(db)


def get_camera_service(db: DbSession) -> CameraService:
    return CameraService(db)
