"""Agent business logic: define agents and execute LangGraph runs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.runtime import AgentRuntime, ChatModel
from app.core.exceptions import AppError
from app.models.agent import Agent
from app.models.agent_run import AgentRun
from app.models.agent_step import AgentStep
from app.repositories.agent import (
    AgentRepository,
    AgentRunRepository,
    AgentStepRepository,
)

_AGENT_NOT_FOUND = "Agent not found"
_RUN_NOT_FOUND = "Run not found"


class AgentService:
    """Manage agent definitions and run them through the LangGraph runtime."""

    def __init__(self, session: AsyncSession, llm: ChatModel) -> None:
        self._session = session
        self._runtime = AgentRuntime(llm)
        self._agents = AgentRepository(session)
        self._runs = AgentRunRepository(session)
        self._steps = AgentStepRepository(session)

    async def create_agent(self, name: str, description: str | None) -> Agent:
        if await self._agents.get_by_name(name) is not None:
            raise AppError("Agent name already exists", status.HTTP_409_CONFLICT)
        agent = await self._agents.create(name, description)
        await self._session.commit()
        await self._session.refresh(agent)
        return agent

    async def list_agents(self) -> list[Agent]:
        return await self._agents.list_all()

    async def run_agent(
        self, user_id: uuid.UUID, agent_id: uuid.UUID, task: str
    ) -> tuple[AgentRun, list[AgentStep]]:
        agent = await self._agents.get_active(agent_id)
        if agent is None:
            raise AppError(_AGENT_NOT_FOUND, status.HTTP_404_NOT_FOUND)

        run = await self._runs.create(agent.id, user_id, {"task": task})
        await self._session.commit()

        try:
            result = await self._runtime.run(task)
        except Exception:
            await self._runs.complete(run, "failed", None, datetime.now(UTC))
            await self._session.commit()
            raise

        await self._steps.bulk_create(run.id, result["steps"])
        await self._runs.complete(
            run,
            "success",
            {"answer": result["answer"], "thought": result["thought"]},
            datetime.now(UTC),
        )
        await self._session.commit()

        steps = await self._steps.list_for_run(run.id)
        await self._session.refresh(run)
        return run, steps

    async def get_run(
        self, user_id: uuid.UUID, run_id: uuid.UUID
    ) -> tuple[AgentRun, list[AgentStep]]:
        run = await self._runs.get_owned(user_id, run_id)
        if run is None:
            raise AppError(_RUN_NOT_FOUND, status.HTTP_404_NOT_FOUND)
        steps = await self._steps.list_for_run(run.id)
        return run, steps
