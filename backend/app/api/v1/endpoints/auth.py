"""Authentication endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession
from app.schemas.auth import LoginRequest, Token, UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token", response_model=Token, summary="OAuth2 password login")
def login_for_token(
    db: DbSession, form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    return AuthService(db).login(form_data.username, form_data.password)


@router.post("/login", response_model=Token, summary="JSON login")
def login_json(db: DbSession, payload: LoginRequest) -> Token:
    return AuthService(db).login(payload.username, payload.password)


@router.post("/register", response_model=UserRead, summary="Create a new operator")
def register_user(db: DbSession, payload: UserCreate, _: CurrentUser) -> UserRead:
    user = AuthService(db).create_user(payload)
    return UserRead.model_validate(user)


@router.get("/me", response_model=UserRead, summary="Current authenticated user")
def read_me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
