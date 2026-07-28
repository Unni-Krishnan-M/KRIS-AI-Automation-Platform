"""Data-access layer for :class:`~app.models.memory.Memory`."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import Memory


class MemoryRepository:
    """Encapsulates all database access for memories."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: uuid.UUID,
        scope: str,
        content: str,
        embedding: list[float],
        importance: float,
    ) -> Memory:
        memory = Memory(
            user_id=user_id,
            scope=scope,
            content=content,
            embedding=embedding,
            importance=importance,
        )
        self._session.add(memory)
        await self._session.flush()
        return memory

    async def get_owned(self, user_id: uuid.UUID, memory_id: uuid.UUID) -> Memory | None:
        result = await self._session.execute(
            select(Memory).where(Memory.id == memory_id, Memory.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID, scope: str | None = None) -> list[Memory]:
        stmt = select(Memory).where(Memory.user_id == user_id)
        if scope is not None:
            stmt = stmt.where(Memory.scope == scope)
        stmt = stmt.order_by(Memory.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search(
        self,
        user_id: uuid.UUID,
        query_embedding: list[float],
        limit: int,
        scope: str | None = None,
    ) -> list[tuple[Memory, float]]:
        distance = Memory.embedding.cosine_distance(query_embedding).label("distance")
        stmt = select(Memory, distance).where(Memory.user_id == user_id)
        if scope is not None:
            stmt = stmt.where(Memory.scope == scope)
        stmt = stmt.order_by(distance).limit(limit)
        result = await self._session.execute(stmt)
        return [(row[0], float(row[1])) for row in result.all()]

    async def touch(self, memories: list[Memory]) -> None:
        """Update ``last_accessed_at`` for the given memories."""
        now = datetime.now(UTC)
        for memory in memories:
            memory.last_accessed_at = now
        await self._session.flush()

    async def delete(self, memory: Memory) -> None:
        await self._session.delete(memory)
        await self._session.flush()
