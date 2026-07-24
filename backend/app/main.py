"""FastAPI application factory and entrypoint.

Run locally with::

    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import health
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.redis import redis_client
from app.db.session import engine
from app.middleware.request_id import RequestIDMiddleware

logger = logging.getLogger("kris")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hooks: configure logging and dispose resources."""
    configure_logging()
    logger.info("KRIS backend starting up")
    yield
    await engine.dispose()
    await redis_client.aclose()
    logger.info("KRIS backend shut down")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(RequestIDMiddleware)
    register_exception_handlers(app)

    # Health at the root (infra convention); versioned business routes under /api/v1.
    app.include_router(health.router)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
