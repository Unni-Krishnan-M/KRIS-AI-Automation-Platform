"""Knowledge-base / RAG request and response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeBaseCreate(BaseModel):
    """Payload for creating a knowledge base."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class KnowledgeBaseRead(BaseModel):
    """Knowledge-base summary."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime


class DocumentRead(BaseModel):
    """Document summary."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    mime_type: str
    status: str
    created_at: datetime


class SearchRequest(BaseModel):
    """Semantic-search query."""

    query: str = Field(min_length=1)
    k: int = Field(default=5, ge=1, le=50)


class SearchResult(BaseModel):
    """A single semantic-search hit."""

    document_id: uuid.UUID
    chunk_index: int
    content: str
    score: float
