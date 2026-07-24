"""Dependency health checks (database, Redis, Ollama).

Each check returns a :class:`ComponentStatus` instead of raising, so a single
degraded dependency never crashes the health endpoint — the caller decides the
HTTP status code from the returned value.
"""

from __future__ import annotations

import httpx
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.schemas.health import ComponentStatus

_OLLAMA_TIMEOUT_SECONDS = 5.0


async def check_database(session: AsyncSession) -> ComponentStatus:
    """Run ``SELECT 1`` to confirm the database is reachable."""
    try:
        await session.execute(text("SELECT 1"))
        return ComponentStatus(status="ok")
    except Exception as exc:  # noqa: BLE001 - surfaced as a health detail
        return ComponentStatus(status="error", detail=str(exc))


async def check_redis(redis: Redis) -> ComponentStatus:
    """Ping Redis to confirm the cache is reachable."""
    try:
        await redis.ping()
        return ComponentStatus(status="ok")
    except Exception as exc:  # noqa: BLE001 - surfaced as a health detail
        return ComponentStatus(status="error", detail=str(exc))


async def check_ollama(settings: Settings) -> ComponentStatus:
    """Query Ollama's ``/api/tags`` to confirm the model server is reachable."""
    url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=_OLLAMA_TIMEOUT_SECONDS) as client:
            response = await client.get(url)
            response.raise_for_status()
        return ComponentStatus(status="ok")
    except Exception as exc:  # noqa: BLE001 - surfaced as a health detail
        return ComponentStatus(status="error", detail=str(exc))
