"""Data-access layer for :class:`~app.models.conversation.Conversation`."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation


class ConversationRepository:
    """Encapsulates all database access for conversations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: uuid.UUID, title: str, model: str) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title, model=model)
        self._session.add(conversation)
        await self._session.flush()
        return conversation

    async def get_owned(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> Conversation | None:
        """Return the conversation only if it belongs to ``user_id``."""
        result = await self._session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID) -> list[Conversation]:
        result = await self._session.execute(
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
            .order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())

    async def soft_delete(self, conversation: Conversation) -> None:
        conversation.deleted_at = datetime.now(UTC)
        await self._session.flush()
