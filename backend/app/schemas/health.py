"""Pydantic schemas for health/readiness responses."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ComponentStatus(BaseModel):
    """Health of a single dependency (database, cache, model server)."""

    status: Literal["ok", "error"]
    detail: str | None = None


class HealthResponse(BaseModel):
    """Liveness response — the process is up and serving requests."""

    status: Literal["ok"]
    app: str
    env: str


class ReadinessResponse(BaseModel):
    """Readiness response — aggregate status of all dependencies."""

    status: Literal["ready", "degraded"]
    components: dict[str, ComponentStatus]
