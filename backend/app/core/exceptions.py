"""Domain-specific exceptions and FastAPI exception handlers.

Keeping error types in one place lets services raise meaningful, layer-agnostic
exceptions while the API layer maps them to consistent HTTP responses.
"""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """Base class for expected, handled application errors."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    message: str = "An application error occurred."

    def __init__(self, message: str | None = None, *, status_code: int | None = None):
        self.message = message or self.message
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    message = "Resource not found."


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    message = "Resource already exists."


class ValidationError(AppError):
    status_code = 422
    message = "Validation failed."


class AuthenticationError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    message = "Could not validate credentials."


class AuthorizationError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    message = "You do not have permission to perform this action."


class VisionError(AppError):
    status_code = 422
    message = "Vision processing failed."


def _error_response(status_code: int, message: str, detail=None) -> JSONResponse:
    payload = {"success": False, "error": message}
    if detail is not None:
        payload["detail"] = detail
    return JSONResponse(status_code=status_code, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach handlers that translate exceptions into JSON envelopes."""

    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError):  # noqa: ANN001
        return _error_response(exc.status_code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(_: Request, exc: RequestValidationError):  # noqa: ANN001
        return _error_response(
            422,
            "Request validation failed.",
            detail=exc.errors(),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(_: Request, exc: Exception):  # noqa: ANN001
        logger.exception("Unhandled error: %s", exc)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "An unexpected internal error occurred.",
        )
