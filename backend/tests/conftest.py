"""Shared pytest fixtures.

Test-only environment variables are set *before* the app is imported so that
``Settings`` construction never fails and no real services are required.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://kris:test@localhost:5432/kris_test")
os.environ.setdefault(
    "DATABASE_SYNC_URL", "postgresql+psycopg2://kris:test@localhost:5432/kris_test"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.main import create_app  # noqa: E402


@pytest.fixture
def app() -> FastAPI:
    """A fresh application instance per test (isolated dependency overrides)."""
    return create_app()


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Async HTTP client wired to the app via ASGI transport (no network)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
