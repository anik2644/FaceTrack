"""Authentication and user provisioning."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Token, UserCreate

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def authenticate(self, username: str, password: str) -> User:
        user = self.users.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Incorrect username or password.")
        if not user.is_active:
            raise AuthenticationError("This account is disabled.")
        return user

    def login(self, username: str, password: str) -> Token:
        user = self.authenticate(username, password)
        token = create_access_token(user.username, {"role": user.role})
        return Token(
            access_token=token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def create_user(self, payload: UserCreate) -> User:
        if self.users.get_by_username(payload.username):
            raise ConflictError("Username already taken.")
        if self.users.get_by_email(payload.email):
            raise ConflictError("Email already registered.")
        user = User(
            username=payload.username,
            email=payload.email,
            full_name=payload.full_name,
            role=payload.role,
            hashed_password=hash_password(payload.password),
        )
        user = self.users.add(user)
        self.users.save()
        return user

    def ensure_bootstrap_admin(self) -> None:
        """Create the default admin account if no users exist yet."""
        if self.users.count() > 0:
            return
        admin = User(
            username=settings.FIRST_ADMIN_USERNAME,
            email=settings.FIRST_ADMIN_EMAIL,
            full_name="Administrator",
            role="admin",
            hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
        )
        self.users.add(admin)
        self.users.save()
        logger.info("Bootstrap admin '%s' created.", settings.FIRST_ADMIN_USERNAME)
