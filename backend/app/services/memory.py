"""Memory business logic: store, recall (semantic), list, delete."""

from __future__ import annotations

import uuid

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.memory import Memory
from app.repositories.memory import MemoryRepository
from app.schemas.memory import MemorySearchResult
from app.services.embeddings import EmbeddingClient

_NOT_FOUND = "Memory not found"


class MemoryService:
    """Store and recall user memories using embedding similarity."""

    def __init__(self, session: AsyncSession, embeddings: EmbeddingClient) -> None:
        self._session = session
        self._embeddings = embeddings
        self._memories = MemoryRepository(session)

    async def add_memory(
        self, user_id: uuid.UUID, content: str, scope: str, importance: float
    ) -> Memory:
        embedding = await self._embeddings.embed_query(content)
        memory = await self._memories.create(user_id, scope, content, embedding, importance)
        await self._session.commit()
        await self._session.refresh(memory)
        return memory

    async def list_memories(self, user_id: uuid.UUID, scope: str | None) -> list[Memory]:
        return await self._memories.list_for_user(user_id, scope)

    async def search_memories(
        self, user_id: uuid.UUID, query: str, k: int, scope: str | None
    ) -> list[MemorySearchResult]:
        query_embedding = await self._embeddings.embed_query(query)
        hits = await self._memories.search(user_id, query_embedding, k, scope)

        # Mark recalled memories as recently accessed.
        await self._memories.touch([memory for memory, _ in hits])
        await self._session.commit()

        return [
            MemorySearchResult(
                id=memory.id,
                scope=memory.scope,
                content=memory.content,
                score=1.0 - distance,
            )
            for memory, distance in hits
        ]

    async def delete_memory(self, user_id: uuid.UUID, memory_id: uuid.UUID) -> None:
        memory = await self._memories.get_owned(user_id, memory_id)
        if memory is None:
            raise AppError(_NOT_FOUND, status.HTTP_404_NOT_FOUND)
        await self._memories.delete(memory)
        await self._session.commit()
