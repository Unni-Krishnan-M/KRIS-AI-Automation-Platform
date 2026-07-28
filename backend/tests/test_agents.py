"""Integration tests for agents and the LangGraph run pipeline.

The LLM is replaced with a deterministic fake so the two-node graph runs
without a model server while still exercising real persistence.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.dependencies.ollama import get_ollama_client

_EMAIL = "agent@example.com"
_PASSWORD = "agent-pass-1234"


class FakeLLM:
    """Returns distinct canned replies for the think vs respond nodes."""

    async def chat(self, messages: list[dict[str, str]], model: str | None = None) -> str:
        system = messages[0]["content"]
        if "reasoning assistant" in system:
            return "The user greeted me, so I should greet back."
        return "Hello there!"


async def _auth_headers(client: AsyncClient) -> dict[str, str]:
    await client.post("/api/v1/auth/register", json={"email": _EMAIL, "password": _PASSWORD})
    login = await client.post("/api/v1/auth/login", json={"email": _EMAIL, "password": _PASSWORD})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _use_fake_llm(app: FastAPI) -> None:
    app.dependency_overrides[get_ollama_client] = lambda: FakeLLM()


async def _create_agent(client: AsyncClient, headers: dict[str, str]) -> str:
    resp = await client.post(
        "/api/v1/agents",
        json={"name": "greeter", "description": "says hi"},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_and_list_agent(app: FastAPI, auth_client: AsyncClient) -> None:
    _use_fake_llm(app)
    headers = await _auth_headers(auth_client)
    await _create_agent(auth_client, headers)

    listed = await auth_client.get("/api/v1/agents", headers=headers)
    assert listed.status_code == 200
    assert [a["name"] for a in listed.json()] == ["greeter"]


@pytest.mark.asyncio
async def test_duplicate_agent_name_conflicts(app: FastAPI, auth_client: AsyncClient) -> None:
    _use_fake_llm(app)
    headers = await _auth_headers(auth_client)
    await _create_agent(auth_client, headers)
    resp = await auth_client.post("/api/v1/agents", json={"name": "greeter"}, headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_run_agent_records_steps_and_output(app: FastAPI, auth_client: AsyncClient) -> None:
    _use_fake_llm(app)
    headers = await _auth_headers(auth_client)
    agent_id = await _create_agent(auth_client, headers)

    run = await auth_client.post(
        f"/api/v1/agents/{agent_id}/run",
        json={"input": "hi"},
        headers=headers,
    )
    assert run.status_code == 201
    body = run.json()
    assert body["status"] == "success"
    assert body["input"] == {"task": "hi"}
    assert body["output"]["answer"] == "Hello there!"
    assert [s["node_name"] for s in body["steps"]] == ["think", "respond"]
    assert body["finished_at"] is not None

    # The run is retrievable afterwards.
    run_id = body["id"]
    fetched = await auth_client.get(f"/api/v1/agents/runs/{run_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == run_id


@pytest.mark.asyncio
async def test_run_unknown_agent_returns_404(app: FastAPI, auth_client: AsyncClient) -> None:
    _use_fake_llm(app)
    headers = await _auth_headers(auth_client)
    missing = "00000000-0000-0000-0000-000000000000"
    resp = await auth_client.post(
        f"/api/v1/agents/{missing}/run",
        json={"input": "hi"},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_unknown_run_returns_404(app: FastAPI, auth_client: AsyncClient) -> None:
    _use_fake_llm(app)
    headers = await _auth_headers(auth_client)
    missing = "00000000-0000-0000-0000-000000000000"
    resp = await auth_client.get(f"/api/v1/agents/runs/{missing}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_agents_require_auth(auth_client: AsyncClient) -> None:
    resp = await auth_client.get("/api/v1/agents")
    assert resp.status_code in (401, 403)
