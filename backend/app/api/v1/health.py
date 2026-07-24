"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.redis import get_redis
from app.db.session import get_db
from app.schemas.health import ComponentStatus, HealthResponse, ReadinessResponse
from app.services.health import check_database, check_ollama, check_redis

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Liveness: the process is up. Never touches external dependencies."""
    return HealthResponse(status="ok", app=settings.app_name, env=settings.app_env)


@router.get("/health/db", response_model=ComponentStatus)
async def health_db(
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> ComponentStatus:
    """Database connectivity check."""
    result = await check_database(session)
    if result.status == "error":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result


@router.get("/health/redis", response_model=ComponentStatus)
async def health_redis(
    response: Response,
    redis: Redis = Depends(get_redis),
) -> ComponentStatus:
    """Redis connectivity check."""
    result = await check_redis(redis)
    if result.status == "error":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result


@router.get("/health/ollama", response_model=ComponentStatus)
async def health_ollama(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> ComponentStatus:
    """Ollama model-server connectivity check."""
    result = await check_ollama(settings)
    if result.status == "error":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result


@router.get("/health/ready", response_model=ReadinessResponse)
async def health_ready(
    response: Response,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> ReadinessResponse:
    """Readiness: aggregate status across all dependencies."""
    components = {
        "database": await check_database(session),
        "redis": await check_redis(redis),
        "ollama": await check_ollama(settings),
    }
    degraded = any(c.status == "error" for c in components.values())
    if degraded:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="degraded" if degraded else "ready",
        components=components,
    )
