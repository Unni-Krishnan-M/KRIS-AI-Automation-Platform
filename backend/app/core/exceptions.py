"""Application-level exceptions and their FastAPI handlers."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger("kris.error")


class AppError(Exception):
    """Base class for expected, handled application errors.

    Raise this (or a subclass) from services to return a controlled HTTP
    response instead of a 500.
    """

    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Return a structured JSON body for handled :class:`AppError`s."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "request_id": _request_id(request)},
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler: log the exception and return a generic 500."""
    logger.exception("Unhandled error", extra={"request_id": _request_id(request)})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "request_id": _request_id(request)},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Wire the handlers above into the FastAPI application."""
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)
