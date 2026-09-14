"""Central logging configuration.

Provides a single ``configure_logging`` entry-point and a ``get_logger``
helper so every module logs through a consistent, timestamped format.
"""
from __future__ import annotations

import logging
import sys
from logging.config import dictConfig

from app.core.config import settings

_CONFIGURED = False


def configure_logging() -> None:
    """Configure root logging once for the whole process."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    level = "DEBUG" if settings.DEBUG else "INFO"
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": sys.stdout,
                }
            },
            "root": {"handlers": ["console"], "level": level},
            "loggers": {
                # Silence noisy third-party frame-by-frame logging.
                "ultralytics": {"level": "WARNING"},
                "uvicorn.access": {"level": "WARNING"},
            },
        }
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for ``name``."""
    configure_logging()
    return logging.getLogger(name)
