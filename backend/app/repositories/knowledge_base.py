"""Data-access layer for :class:`~app.models.knowledge_base.KnowledgeBase`."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KnowledgeBase


class KnowledgeBaseRepository:
    """Encapsulates all database access for knowledge bases."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: uuid.UUID, name: str, description: str | None) -> KnowledgeBase:
        knowledge_base = KnowledgeBase(user_id=user_id, name=name, description=description)
        self._session.add(knowledge_base)
        await self._session.flush()
        return knowledge_base

    async def get_owned(
        self, user_id: uuid.UUID, knowledge_base_id: uuid.UUID
    ) -> KnowledgeBase | None:
        result = await self._session.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == knowledge_base_id,
                KnowledgeBase.user_id == user_id,
                KnowledgeBase.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID) -> list[KnowledgeBase]:
        result = await self._session.execute(
            select(KnowledgeBase)
            .where(
                KnowledgeBase.user_id == user_id,
                KnowledgeBase.deleted_at.is_(None),
            )
            .order_by(KnowledgeBase.created_at.desc())
        )
        return list(result.scalars().all())
