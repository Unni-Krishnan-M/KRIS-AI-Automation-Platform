"""Memory ORM model — long/short-term memories with an embedding."""

from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin

EMBEDDING_DIM = 768


class Memory(UUIDMixin, TimestampMixin, Base):
    """A recalled fact/context tied to a user, retrievable by similarity."""

    __tablename__ = "memories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # One of: short | long
    scope: Mapped[str] = mapped_column(
        String(20), default="long", server_default="long", nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    importance: Mapped[float] = mapped_column(
        Float, default=1.0, server_default="1.0", nullable=False
    )
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
