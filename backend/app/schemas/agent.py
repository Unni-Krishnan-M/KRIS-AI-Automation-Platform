"""Agent request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentCreate(BaseModel):
    """Payload for defining a new agent."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class AgentRead(BaseModel):
    """Agent definition summary."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime


class AgentRunRequest(BaseModel):
    """Task input for an agent run."""

    input: str = Field(min_length=1)


class AgentStepRead(BaseModel):
    """A single recorded step of a run."""

    model_config = ConfigDict(from_attributes=True)

    step_index: int
    node_name: str
    output: dict[str, Any] | None


class AgentRunRead(BaseModel):
    """An agent run with its steps."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    status: str
    input: dict[str, Any]
    output: dict[str, Any] | None
    created_at: datetime
    finished_at: datetime | None
    steps: list[AgentStepRead]
