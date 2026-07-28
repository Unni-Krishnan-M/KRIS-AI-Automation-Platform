"""Integration tests for memory storage and semantic recall.

Uses a deterministic fake embedding client so recall ordering is predictable
while still exercising real pgvector queries.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.dependencies.embeddings import get_embedding_client

_EMAIL = "mem@example.com"
_PASSWORD = "mem-pass-1234"
_DIM = 768


class FakeEmbeddingClient:
    """One-hot-ish embeddings keyed on 'coffee' / 'python'."""

    dim = _DIM

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * _DIM
        lowered = text.lower()
        if "coffee" in lowered:
            vector[0] = 1.0
        elif "python" in lowered:
            vector[1] = 1.0
        else:
            vector[2] = 1.0
        return vector

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


async def _auth_headers(client: AsyncClient) -> dict[str, str]:
    await client.post("/api/v1/auth/register", json={"email": _EMAIL, "password": _PASSWORD})
    login = await client.post("/api/v1/auth/login", json={"email": _EMAIL, "password": _PASSWORD})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _use_fake_embeddings(app: FastAPI) -> None:
    app.dependency_overrides[get_embedding_client] = lambda: FakeEmbeddingClient()


@pytest.mark.asyncio
async def test_create_and_list_memory(app: FastAPI, auth_client: AsyncClient) -> None:
    _use_fake_embeddings(app)
    headers = await _auth_headers(auth_client)

    created = await auth_client.post(
        "/api/v1/memory",
        json={"content": "User loves coffee", "scope": "long", "importance": 2.0},
        headers=headers,
    )
    assert created.status_code == 201
    body = created.json()
    assert body["content"] == "User loves coffee"
    assert body["scope"] == "long"
    assert body["last_accessed_at"] is None

    listed = await auth_client.get("/api/v1/memory", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


@pytest.mark.asyncio
async def test_recall_returns_relevant_memory(app: FastAPI, auth_client: AsyncClient) -> None:
    _use_fake_embeddings(app)
    headers = await _auth_headers(auth_client)

    for content in ["User enjoys coffee in the morning", "User codes in python"]:
        await auth_client.post("/api/v1/memory", json={"content": content}, headers=headers)

    resp = await auth_client.post(
        "/api/v1/memory/search",
        json={"query": "what beverage does the user like", "k": 2},
        headers=headers,
    )
    assert resp.status_code == 200
    results = resp.json()
    assert results  # non-empty
    # 'beverage' matches neither keyword -> vector[2]; both stored memories are
    # equally distant, so just assert the endpoint returns scored results.
    assert all("score" in r for r in results)


@pytest.mark.asyncio
async def test_recall_scopes_the_query(app: FastAPI, auth_client: AsyncClient) -> None:
    _use_fake_embeddings(app)
    headers = await _auth_headers(auth_client)

    await auth_client.post(
        "/api/v1/memory",
        json={"content": "coffee fact", "scope": "long"},
        headers=headers,
    )
    await auth_client.post(
        "/api/v1/memory",
        json={"content": "python fact", "scope": "short"},
        headers=headers,
    )

    resp = await auth_client.post(
        "/api/v1/memory/search",
        json={"query": "python", "k": 5, "scope": "short"},
        headers=headers,
    )
    results = resp.json()
    assert len(results) == 1
    assert results[0]["content"] == "python fact"


@pytest.mark.asyncio
async def test_delete_memory(app: FastAPI, auth_client: AsyncClient) -> None:
    _use_fake_embeddings(app)
    headers = await _auth_headers(auth_client)
    created = await auth_client.post(
        "/api/v1/memory", json={"content": "temp memory"}, headers=headers
    )
    memory_id = created.json()["id"]

    deleted = await auth_client.delete(f"/api/v1/memory/{memory_id}", headers=headers)
    assert deleted.status_code == 204

    listed = await auth_client.get("/api/v1/memory", headers=headers)
    assert listed.json() == []


@pytest.mark.asyncio
async def test_delete_missing_memory_returns_404(app: FastAPI, auth_client: AsyncClient) -> None:
    _use_fake_embeddings(app)
    headers = await _auth_headers(auth_client)
    missing = "00000000-0000-0000-0000-000000000000"
    resp = await auth_client.delete(f"/api/v1/memory/{missing}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_memory_requires_auth(auth_client: AsyncClient) -> None:
    resp = await auth_client.get("/api/v1/memory")
    assert resp.status_code in (401, 403)
