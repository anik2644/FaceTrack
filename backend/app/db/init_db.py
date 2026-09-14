"""Database bootstrap: create tables and the default admin user."""
from __future__ import annotations

from app.core.logging import get_logger
from app.db.base import Base
from app.db.session import SessionLocal, engine

# Import models so their tables register on Base.metadata.
import app.models  # noqa: F401  (side-effect import)

logger = get_logger(__name__)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")

    from app.services.auth_service import AuthService

    db = SessionLocal()
    try:
        AuthService(db).ensure_bootstrap_admin()
    finally:
        db.close()
