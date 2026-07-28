"""Data-access layer for agents, runs, and steps."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.agent_run import AgentRun
from app.models.agent_step import AgentStep


class AgentRepository:
    """Database access for agent definitions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, name: str, description: str | None) -> Agent:
        agent = Agent(name=name, description=description)
        self._session.add(agent)
        await self._session.flush()
        return agent

    async def get_active(self, agent_id: uuid.UUID) -> Agent | None:
        agent = await self._session.get(Agent, agent_id)
        if agent is None or not agent.is_active:
            return None
        return agent

    async def get_by_name(self, name: str) -> Agent | None:
        result = await self._session.execute(select(Agent).where(Agent.name == name))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Agent]:
        result = await self._session.execute(select(Agent).order_by(Agent.created_at.desc()))
        return list(result.scalars().all())


class AgentRunRepository:
    """Database access for agent runs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, agent_id: uuid.UUID, user_id: uuid.UUID, input_payload: dict[str, Any]
    ) -> AgentRun:
        run = AgentRun(agent_id=agent_id, user_id=user_id, input=input_payload)
        self._session.add(run)
        await self._session.flush()
        return run

    async def complete(
        self,
        run: AgentRun,
        status: str,
        output: dict[str, Any] | None,
        finished_at: datetime,
    ) -> None:
        run.status = status
        run.output = output
        run.finished_at = finished_at
        await self._session.flush()

    async def get_owned(self, user_id: uuid.UUID, run_id: uuid.UUID) -> AgentRun | None:
        result = await self._session.execute(
            select(AgentRun).where(AgentRun.id == run_id, AgentRun.user_id == user_id)
        )
        return result.scalar_one_or_none()


class AgentStepRepository:
    """Database access for agent steps."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_create(self, run_id: uuid.UUID, steps: list[dict[str, Any]]) -> None:
        for index, step in enumerate(steps):
            self._session.add(
                AgentStep(
                    run_id=run_id,
                    step_index=index,
                    node_name=str(step.get("node", "")),
                    output={"content": step.get("output")},
                )
            )
        await self._session.flush()

    async def list_for_run(self, run_id: uuid.UUID) -> list[AgentStep]:
        result = await self._session.execute(
            select(AgentStep).where(AgentStep.run_id == run_id).order_by(AgentStep.step_index.asc())
        )
        return list(result.scalars().all())
