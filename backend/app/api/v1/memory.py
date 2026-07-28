"""Memory endpoints (all require an authenticated user)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.embeddings import get_embedding_client
from app.models.user import User
from app.schemas.memory import (
    MemoryCreate,
    MemoryRead,
    MemoryScope,
    MemorySearchRequest,
    MemorySearchResult,
)
from app.services.embeddings import EmbeddingClient
from app.services.memory import MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])


def _service(session: AsyncSession, embeddings: EmbeddingClient) -> MemoryService:
    return MemoryService(session, embeddings)


@router.get("", response_model=list[MemoryRead])
async def list_memories(
    scope: MemoryScope | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    embeddings: EmbeddingClient = Depends(get_embedding_client),
) -> list[MemoryRead]:
    memories = await _service(session, embeddings).list_memories(current_user.id, scope)
    return [MemoryRead.model_validate(m) for m in memories]


@router.post("", response_model=MemoryRead, status_code=status.HTTP_201_CREATED)
async def create_memory(
    payload: MemoryCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    embeddings: EmbeddingClient = Depends(get_embedding_client),
) -> MemoryRead:
    memory = await _service(session, embeddings).add_memory(
        current_user.id, payload.content, payload.scope, payload.importance
    )
    return MemoryRead.model_validate(memory)


@router.post("/search", response_model=list[MemorySearchResult])
async def search_memories(
    payload: MemorySearchRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    embeddings: EmbeddingClient = Depends(get_embedding_client),
) -> list[MemorySearchResult]:
    return await _service(session, embeddings).search_memories(
        current_user.id, payload.query, payload.k, payload.scope
    )


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    embeddings: EmbeddingClient = Depends(get_embedding_client),
) -> None:
    await _service(session, embeddings).delete_memory(current_user.id, memory_id)
