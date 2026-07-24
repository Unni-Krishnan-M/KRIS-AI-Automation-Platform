"""Data-access layer for :class:`~app.models.user.User`."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Encapsulates all database access for users."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        """Return the active (non-deleted) user with ``email``, if any."""
        result = await self._session.execute(
            select(User).where(User.email == email, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Return the user with ``user_id``, or ``None``."""
        user = await self._session.get(User, user_id)
        if user is None or user.deleted_at is not None:
            return None
        return user

    async def create(self, user: User) -> User:
        """Add ``user`` to the session and flush to assign its id."""
        self._session.add(user)
        await self._session.flush()
        return user
