"""User ORM model.

The table schema lives here (Milestone 2 — Database Layer). Authentication
behaviour (password hashing, token issuance, endpoints) is added on top in
Milestone 3, which also introduces ``refresh_tokens`` and ``api_keys``.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    """An application user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), default=None)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    def __repr__(self) -> str:
        return f"<User id={self.id!r} email={self.email!r}>"
