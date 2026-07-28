"""Agent endpoints (all require an authenticated user)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.ollama import get_ollama_client
from app.models.agent_run import AgentRun
from app.models.agent_step import AgentStep
from app.models.user import User
from app.schemas.agent import (
    AgentCreate,
    AgentRead,
    AgentRunRead,
    AgentRunRequest,
    AgentStepRead,
)
from app.services.agent import AgentService
from app.services.ollama import OllamaClient

router = APIRouter(prefix="/agents", tags=["agents"])


def _service(session: AsyncSession, llm: OllamaClient) -> AgentService:
    return AgentService(session, llm)


def _to_run_read(run: AgentRun, steps: list[AgentStep]) -> AgentRunRead:
    return AgentRunRead(
        id=run.id,
        agent_id=run.agent_id,
        status=run.status,
        input=run.input,
        output=run.output,
        created_at=run.created_at,
        finished_at=run.finished_at,
        steps=[AgentStepRead.model_validate(s) for s in steps],
    )


@router.get("", response_model=list[AgentRead])
async def list_agents(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    llm: OllamaClient = Depends(get_ollama_client),
) -> list[AgentRead]:
    agents = await _service(session, llm).list_agents()
    return [AgentRead.model_validate(a) for a in agents]


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent(
    payload: AgentCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    llm: OllamaClient = Depends(get_ollama_client),
) -> AgentRead:
    agent = await _service(session, llm).create_agent(payload.name, payload.description)
    return AgentRead.model_validate(agent)


@router.get("/runs/{run_id}", response_model=AgentRunRead)
async def get_run(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    llm: OllamaClient = Depends(get_ollama_client),
) -> AgentRunRead:
    run, steps = await _service(session, llm).get_run(current_user.id, run_id)
    return _to_run_read(run, steps)


@router.post(
    "/{agent_id}/run",
    response_model=AgentRunRead,
    status_code=status.HTTP_201_CREATED,
)
async def run_agent(
    agent_id: uuid.UUID,
    payload: AgentRunRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    llm: OllamaClient = Depends(get_ollama_client),
) -> AgentRunRead:
    run, steps = await _service(session, llm).run_agent(current_user.id, agent_id, payload.input)
    return _to_run_read(run, steps)
