"""Application configuration.

Centralised, type-safe settings loaded from environment variables (and an
optional ``.env`` file) via :mod:`pydantic-settings`. Importing ``settings``
anywhere in the app gives a single, validated source of truth.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve important on-disk locations relative to the backend package root so
# the app behaves the same regardless of the current working directory.
BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----- Application -----------------------------------------------------
    APP_NAME: str = "FaceTrack"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "Real-time CCTV-based person detection and face-recognition "
        "attendance platform."
    )
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # ----- Server ----------------------------------------------------------
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ----- Security --------------------------------------------------------
    SECRET_KEY: str = "CHANGE-ME-super-secret-key-for-jwt-signing"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    # Default bootstrap admin (created on first run if no users exist).
    FIRST_ADMIN_USERNAME: str = "admin"
    FIRST_ADMIN_PASSWORD: str = "admin123"
    FIRST_ADMIN_EMAIL: str = "admin@facetrack.io"

    # ----- CORS ------------------------------------------------------------
    # Stored as a raw comma-separated string so pydantic-settings does not try
    # to JSON-decode it from the .env file; use ``cors_origins`` for the list.
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ----- Database --------------------------------------------------------
    DATABASE_URL: str = f"sqlite:///{PROJECT_ROOT / 'database' / 'attendance.db'}"

    # ----- Storage ---------------------------------------------------------
    STORAGE_DIR: Path = BACKEND_ROOT / "storage"
    FACES_DIR: Path = BACKEND_ROOT / "storage" / "faces"
    SNAPSHOTS_DIR: Path = BACKEND_ROOT / "storage" / "snapshots"

    # ----- Vision / ML -----------------------------------------------------
    YOLO_MODEL_PATH: str = str(BACKEND_ROOT / "ml_models" / "yolov8n.pt")
    YOLO_CONFIDENCE: float = 0.4
    # Face distance below which two encodings are considered the same person.
    FACE_MATCH_TOLERANCE: float = 0.55
    # Minimum recognition confidence (1 - distance) to accept a match.
    FACE_RECOGNITION_THRESHOLD: float = 0.45
    # Process every Nth frame for the heavy recognition step.
    FRAME_SKIP: int = 2
    JPEG_QUALITY: int = 65
    # Cooldown (seconds) before the same person is marked present again.
    ATTENDANCE_COOLDOWN_SECONDS: int = 60
    # Standard work-day start; arrivals after this are flagged "late".
    WORKDAY_START: str = "09:15"

    @property
    def cors_origins(self) -> List[str]:
        """CORS origins as a list, parsed from the comma-separated string."""
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    def ensure_directories(self) -> None:
        """Create runtime directories if they do not yet exist."""
        for directory in (self.STORAGE_DIR, self.FACES_DIR, self.SNAPSHOTS_DIR):
            Path(directory).mkdir(parents=True, exist_ok=True)
        # Ensure the SQLite parent directory exists.
        if self.DATABASE_URL.startswith("sqlite"):
            db_path = self.DATABASE_URL.split("///", 1)[-1]
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings


settings = get_settings()
