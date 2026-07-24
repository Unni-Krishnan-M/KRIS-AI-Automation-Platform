"""Refresh-token ORM model.

One row per issued refresh token. The ``jti`` (JWT id) uniquely identifies the
token so it can be revoked; tokens are rotated (old one revoked, new one issued)
on every refresh.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class RefreshToken(UUIDMixin, TimestampMixin, Base):
    """A persisted, revocable refresh token."""

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
