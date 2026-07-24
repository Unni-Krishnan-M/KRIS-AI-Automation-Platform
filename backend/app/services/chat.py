"""Chat business logic: conversation management and streamed completions."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.services.ollama import OllamaClient

_NOT_FOUND = "Conversation not found"


class ChatService:
    """Create/list/read/delete conversations and stream assistant replies."""

    def __init__(self, session: AsyncSession, ollama: OllamaClient) -> None:
        self._session = session
        self._ollama = ollama
        self._conversations = ConversationRepository(session)
        self._messages = MessageRepository(session)

    async def create_conversation(self, user_id: uuid.UUID, title: str, model: str) -> Conversation:
        conversation = await self._conversations.create(user_id, title, model)
        await self._session.commit()
        await self._session.refresh(conversation)
        return conversation

    async def list_conversations(self, user_id: uuid.UUID) -> list[Conversation]:
        return await self._conversations.list_for_user(user_id)

    async def get_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> tuple[Conversation, list[Message]]:
        conversation = await self._require_owned(user_id, conversation_id)
        messages = await self._messages.list_for_conversation(conversation_id)
        return conversation, messages

    async def delete_conversation(self, user_id: uuid.UUID, conversation_id: uuid.UUID) -> None:
        conversation = await self._require_owned(user_id, conversation_id)
        await self._conversations.soft_delete(conversation)
        await self._session.commit()

    async def stream_reply(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID, content: str
    ) -> AsyncIterator[str]:
        """Persist the user message, stream the assistant reply, then persist it."""
        conversation = await self._require_owned(user_id, conversation_id)

        await self._messages.create(conversation_id, "user", content)
        await self._session.commit()

        history = await self._messages.list_for_conversation(conversation_id)
        payload = [{"role": m.role, "content": m.content} for m in history]

        parts: list[str] = []
        try:
            async for chunk in self._ollama.chat_stream(payload, conversation.model):
                parts.append(chunk)
                yield chunk
        finally:
            # Persist whatever was generated, even on early client disconnect.
            if parts:
                await self._messages.create(conversation_id, "assistant", "".join(parts))
                await self._session.commit()

    async def _require_owned(self, user_id: uuid.UUID, conversation_id: uuid.UUID) -> Conversation:
        conversation = await self._conversations.get_owned(user_id, conversation_id)
        if conversation is None:
            raise AppError(_NOT_FOUND, status.HTTP_404_NOT_FOUND)
        return conversation
