"""Tests for the health/readiness endpoints and request-ID middleware.

Dependency checks (db/redis/ollama) are exercised with dependency overrides so
the suite is hermetic and needs no running services.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.db.session import get_db


@pytest.mark.asyncio
async def test_liveness_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body == {"status": "ok", "app": "KRIS", "env": "development"}


@pytest.mark.asyncio
async def test_response_carries_request_id(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_inbound_request_id_is_echoed(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"X-Request-ID": "abc-123"})

    assert response.headers["X-Request-ID"] == "abc-123"


@pytest.mark.asyncio
async def test_health_db_ok_with_overridden_session(app: FastAPI, client: AsyncClient) -> None:
    fake_session = AsyncMock()
    fake_session.execute = AsyncMock(return_value=None)

    async def override_get_db() -> AsyncIterator[AsyncMock]:
        yield fake_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await client.get("/health/db")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "detail": None}
    fake_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_health_db_error_returns_503(app: FastAPI, client: AsyncClient) -> None:
    fake_session = AsyncMock()
    fake_session.execute = AsyncMock(side_effect=RuntimeError("connection refused"))

    async def override_get_db() -> AsyncIterator[AsyncMock]:
        yield fake_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = await client.get("/health/db")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert "connection refused" in body["detail"]
