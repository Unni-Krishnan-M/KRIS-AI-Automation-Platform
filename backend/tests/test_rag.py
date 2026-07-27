"""Integration tests for knowledge bases and semantic search.

The embedding client is replaced with a deterministic fake so vector search is
predictable while still exercising real pgvector queries.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.dependencies.embeddings import get_embedding_client

_EMAIL = "rag@example.com"
_PASSWORD = "rag-pass-1234"
_DIM = 768


class FakeEmbeddingClient:
    """One-hot-ish embeddings keyed on the words 'cat' / 'dog'."""

    dim = _DIM

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * _DIM
        lowered = text.lower()
        if "cat" in lowered:
            vector[0] = 1.0
        elif "dog" in lowered:
            vector[1] = 1.0
        else:
            vector[2] = 1.0
        return vector

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


async def _auth_headers(client: AsyncClient) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"email": _EMAIL, "password": _PASSWORD},
    )
    login = await client.post("/api/v1/auth/login", json={"email": _EMAIL, "password": _PASSWORD})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _use_fake_embeddings(app: FastAPI) -> None:
    app.dependency_overrides[get_embedding_client] = lambda: FakeEmbeddingClient()


@pytest.mark.asyncio
async def test_create_and_list_knowledge_base(auth_client: AsyncClient) -> None:
    headers = await _auth_headers(auth_client)
    created = await auth_client.post("/api/v1/knowledge", json={"name": "Docs"}, headers=headers)
    assert created.status_code == 201
    assert created.json()["name"] == "Docs"

    listed = await auth_client.get("/api/v1/knowledge", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


@pytest.mark.asyncio
async def test_upload_document_processes_chunks(app: FastAPI, auth_client: AsyncClient) -> None:
    _use_fake_embeddings(app)
    headers = await _auth_headers(auth_client)
    kb = await auth_client.post("/api/v1/knowledge", json={"name": "Animals"}, headers=headers)
    kb_id = kb.json()["id"]

    resp = await auth_client.post(
        f"/api/v1/knowledge/{kb_id}/documents",
        files={"file": ("cats.txt", b"Cats are wonderful pets.", "text/plain")},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "processed"

    docs = await auth_client.get(f"/api/v1/knowledge/{kb_id}/documents", headers=headers)
    assert len(docs.json()) == 1


@pytest.mark.asyncio
async def test_semantic_search_returns_relevant_chunk(
    app: FastAPI, auth_client: AsyncClient
) -> None:
    _use_fake_embeddings(app)
    headers = await _auth_headers(auth_client)
    kb = await auth_client.post("/api/v1/knowledge", json={"name": "Animals"}, headers=headers)
    kb_id = kb.json()["id"]

    for name, body in [
        ("cats.txt", b"Cats are independent and love to nap."),
        ("dogs.txt", b"Dogs are loyal and enjoy walks."),
    ]:
        await auth_client.post(
            f"/api/v1/knowledge/{kb_id}/documents",
            files={"file": (name, body, "text/plain")},
            headers=headers,
        )

    resp = await auth_client.post(
        f"/api/v1/knowledge/{kb_id}/search",
        json={"query": "tell me about cats", "k": 1},
        headers=headers,
    )
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert "Cats" in results[0]["content"]
    assert results[0]["score"] == pytest.approx(1.0, abs=1e-6)


@pytest.mark.asyncio
async def test_search_missing_kb_returns_404(auth_client: AsyncClient) -> None:
    headers = await _auth_headers(auth_client)
    missing = "00000000-0000-0000-0000-000000000000"
    resp = await auth_client.post(
        f"/api/v1/knowledge/{missing}/search",
        json={"query": "x"},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_knowledge_requires_auth(auth_client: AsyncClient) -> None:
    resp = await auth_client.get("/api/v1/knowledge")
    assert resp.status_code in (401, 403)
