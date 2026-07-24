"""Integration tests for chat conversations and streaming.

The Ollama client is replaced with a fake so tests need no model server.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.dependencies.ollama import get_ollama_client

_EMAIL = "chatter@example.com"
_PASSWORD = "chat-pass-1234"


class FakeOllamaClient:
    """Yields a fixed set of deltas instead of calling a real model."""

    def __init__(self, chunks: list[str] | None = None) -> None:
        self._chunks = chunks or ["Hello", ", ", "world", "!"]

    async def chat_stream(
        self, messages: list[dict[str, str]], model: str | None = None
    ) -> AsyncIterator[str]:
        for chunk in self._chunks:
            yield chunk


async def _auth_headers(client: AsyncClient) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"email": _EMAIL, "password": _PASSWORD, "full_name": "Chatter"},
    )
    login = await client.post("/api/v1/auth/login", json={"email": _EMAIL, "password": _PASSWORD})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_and_list_conversation(auth_client: AsyncClient) -> None:
    headers = await _auth_headers(auth_client)

    created = await auth_client.post(
        "/api/v1/chat/conversations", json={"title": "My chat"}, headers=headers
    )
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "My chat"
    assert body["model"]  # defaulted from settings

    listed = await auth_client.get("/api/v1/chat/conversations", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


@pytest.mark.asyncio
async def test_conversations_require_auth(auth_client: AsyncClient) -> None:
    resp = await auth_client.get("/api/v1/chat/conversations")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_stream_message_persists_both_messages(
    app: FastAPI, auth_client: AsyncClient
) -> None:
    app.dependency_overrides[get_ollama_client] = lambda: FakeOllamaClient()
    headers = await _auth_headers(auth_client)

    conv = await auth_client.post(
        "/api/v1/chat/conversations", json={"title": "Stream"}, headers=headers
    )
    conv_id = conv.json()["id"]

    resp = await auth_client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        json={"content": "Hi there"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert "Hello" in resp.text
    assert "[DONE]" in resp.text

    detail = await auth_client.get(f"/api/v1/chat/conversations/{conv_id}", headers=headers)
    messages = detail.json()["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "Hi there"
    assert messages[1]["content"] == "Hello, world!"


@pytest.mark.asyncio
async def test_get_missing_conversation_returns_404(auth_client: AsyncClient) -> None:
    headers = await _auth_headers(auth_client)
    missing = "00000000-0000-0000-0000-000000000000"
    resp = await auth_client.get(f"/api/v1/chat/conversations/{missing}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_conversation(auth_client: AsyncClient) -> None:
    headers = await _auth_headers(auth_client)
    conv = await auth_client.post(
        "/api/v1/chat/conversations", json={"title": "Temp"}, headers=headers
    )
    conv_id = conv.json()["id"]

    deleted = await auth_client.delete(f"/api/v1/chat/conversations/{conv_id}", headers=headers)
    assert deleted.status_code == 204

    after = await auth_client.get("/api/v1/chat/conversations", headers=headers)
    assert after.json() == []
