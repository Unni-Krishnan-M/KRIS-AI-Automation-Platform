"""Chat request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    """Payload for starting a new conversation."""

    title: str = Field(default="New conversation", max_length=255)
    model: str | None = Field(default=None, max_length=100)


class ConversationRead(BaseModel):
    """Conversation summary (no messages)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    model: str
    created_at: datetime
    updated_at: datetime


class MessageRead(BaseModel):
    """A single message."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    created_at: datetime


class ConversationDetail(ConversationRead):
    """Conversation including its messages."""

    messages: list[MessageRead]


class ChatMessageRequest(BaseModel):
    """A user message to send to the assistant."""

    content: str = Field(min_length=1)
