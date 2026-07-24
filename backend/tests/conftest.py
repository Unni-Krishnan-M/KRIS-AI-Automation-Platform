"""Shared pytest fixtures.

Local ``backend/.env`` values are loaded first (so integration tests hit the
real dev database); any values still missing fall back to harmless test
defaults so the app imports and hermetic tests run even with no ``.env`` or
services (e.g. in CI).
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _value = _line.split("=", 1)
            os.environ.setdefault(_key.strip(), _value.strip())

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
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
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


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """A transaction-isolated DB session (rolled back after each test).

    Skips the test if PostgreSQL is not reachable, so hermetic tests still run
    in environments without a database.
    """
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    try:
        # Ensure the schema exists (own committed transaction), then open a
        # separate transaction for the test to roll back.
        async with engine.begin() as ddl_conn:
            await ddl_conn.run_sync(Base.metadata.create_all)
    except Exception:  # noqa: BLE001 - unreachable DB -> skip, not fail
        await engine.dispose()
        pytest.skip("PostgreSQL not reachable for integration tests")

    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        await session.close()
        if transaction.is_active:
            await transaction.rollback()
        await connection.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def auth_client(app: FastAPI, db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """HTTP client whose requests share the transaction-isolated session."""

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()
