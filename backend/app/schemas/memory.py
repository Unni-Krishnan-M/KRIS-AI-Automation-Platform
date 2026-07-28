"""Memory request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MemoryScope = Literal["short", "long"]


class MemoryCreate(BaseModel):
    """Payload for storing a new memory."""

    content: str = Field(min_length=1)
    scope: MemoryScope = "long"
    importance: float = Field(default=1.0, ge=0.0, le=10.0)


class MemoryRead(BaseModel):
    """A stored memory."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scope: str
    content: str
    importance: float
    last_accessed_at: datetime | None
    created_at: datetime


class MemorySearchRequest(BaseModel):
    """Semantic recall query."""

    query: str = Field(min_length=1)
    k: int = Field(default=5, ge=1, le=50)
    scope: MemoryScope | None = None


class MemorySearchResult(BaseModel):
    """A single recalled memory with its similarity score."""

    id: uuid.UUID
    scope: str
    content: str
    score: float
