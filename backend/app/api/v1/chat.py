"""Chat endpoints (all require an authenticated user)."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.ollama import get_ollama_client
from app.models.user import User
from app.schemas.chat import (
    ChatMessageRequest,
    ConversationCreate,
    ConversationDetail,
    ConversationRead,
    MessageRead,
)
from app.services.chat import ChatService
from app.services.ollama import OllamaClient

router = APIRouter(prefix="/chat", tags=["chat"])


def _service(session: AsyncSession, ollama: OllamaClient) -> ChatService:
    return ChatService(session, ollama)


@router.get("/conversations", response_model=list[ConversationRead])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    ollama: OllamaClient = Depends(get_ollama_client),
) -> list[ConversationRead]:
    conversations = await _service(session, ollama).list_conversations(current_user.id)
    return [ConversationRead.model_validate(c) for c in conversations]


@router.post(
    "/conversations",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    ollama: OllamaClient = Depends(get_ollama_client),
) -> ConversationRead:
    model = payload.model or get_settings().ollama_chat_model
    conversation = await _service(session, ollama).create_conversation(
        current_user.id, payload.title, model
    )
    return ConversationRead.model_validate(conversation)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    ollama: OllamaClient = Depends(get_ollama_client),
) -> ConversationDetail:
    conversation, messages = await _service(session, ollama).get_conversation(
        current_user.id, conversation_id
    )
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        model=conversation.model,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[MessageRead.model_validate(m) for m in messages],
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    ollama: OllamaClient = Depends(get_ollama_client),
) -> None:
    await _service(session, ollama).delete_conversation(current_user.id, conversation_id)


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: uuid.UUID,
    payload: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    ollama: OllamaClient = Depends(get_ollama_client),
) -> StreamingResponse:
    """Send a user message and stream the assistant reply as Server-Sent Events."""
    service = _service(session, ollama)

    async def event_stream() -> AsyncIterator[str]:
        async for delta in service.stream_reply(current_user.id, conversation_id, payload.content):
            yield f"data: {json.dumps({'delta': delta})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
