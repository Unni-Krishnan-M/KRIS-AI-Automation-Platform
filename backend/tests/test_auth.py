"""Integration tests for the authentication flow.

These run against the real dev database using a transaction that is rolled back
after each test (see ``db_session`` in conftest), so nothing persists.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

_EMAIL = "alice@example.com"
_PASSWORD = "sup3r-secret-pw"


async def _register(client: AsyncClient, email: str = _EMAIL) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": _PASSWORD, "full_name": "Alice"},
    )
    assert resp.status_code == 201, resp.text


@pytest.mark.asyncio
async def test_register_returns_user_without_password(auth_client: AsyncClient) -> None:
    resp = await auth_client.post(
        "/api/v1/auth/register",
        json={"email": _EMAIL, "password": _PASSWORD, "full_name": "Alice"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == _EMAIL
    assert body["is_active"] is True
    assert "hashed_password" not in body
    assert "password" not in body


@pytest.mark.asyncio
async def test_register_duplicate_email_conflicts(auth_client: AsyncClient) -> None:
    await _register(auth_client)
    resp = await auth_client.post(
        "/api/v1/auth/register",
        json={"email": _EMAIL, "password": _PASSWORD},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success_returns_tokens(auth_client: AsyncClient) -> None:
    await _register(auth_client)
    resp = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": _EMAIL, "password": _PASSWORD},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


@pytest.mark.asyncio
async def test_login_wrong_password_unauthorized(auth_client: AsyncClient) -> None:
    await _register(auth_client)
    resp = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": _EMAIL, "password": "wrong-password"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user(auth_client: AsyncClient) -> None:
    await _register(auth_client)
    login = await auth_client.post(
        "/api/v1/auth/login", json={"email": _EMAIL, "password": _PASSWORD}
    )
    access = login.json()["access_token"]

    resp = await auth_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == _EMAIL


@pytest.mark.asyncio
async def test_me_without_token_is_rejected(auth_client: AsyncClient) -> None:
    resp = await auth_client.get("/api/v1/auth/me")
    # HTTPBearer rejects missing credentials (401 or 403 depending on version).
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_refresh_rotates_and_old_token_is_revoked(
    auth_client: AsyncClient,
) -> None:
    await _register(auth_client)
    login = await auth_client.post(
        "/api/v1/auth/login", json={"email": _EMAIL, "password": _PASSWORD}
    )
    old_refresh = login.json()["refresh_token"]

    first = await auth_client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert first.status_code == 200
    assert first.json()["access_token"]

    # Reusing the rotated (now revoked) refresh token must fail.
    reuse = await auth_client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse.status_code == 401
