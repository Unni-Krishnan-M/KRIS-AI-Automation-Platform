"""Async SQLAlchemy engine and session management.

The ORM models and migrations arrive in Milestone 2; this module provides the
async engine and session factory that the rest of the app depends on, plus the
``get_db`` FastAPI dependency.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session, closing it when the request ends."""
    async with AsyncSessionLocal() as session:
        yield session
