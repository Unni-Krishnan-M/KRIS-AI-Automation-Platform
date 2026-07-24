"""Data-access layer for :class:`~app.models.refresh_token.RefreshToken`."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Encapsulates all database access for refresh tokens."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: uuid.UUID, jti: str, expires_at: datetime) -> RefreshToken:
        """Persist a new refresh-token record."""
        token = RefreshToken(user_id=user_id, jti=jti, expires_at=expires_at)
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        """Return the refresh-token record for ``jti``, if any."""
        result = await self._session.execute(select(RefreshToken).where(RefreshToken.jti == jti))
        return result.scalar_one_or_none()

    async def revoke(self, token: RefreshToken) -> None:
        """Mark a refresh token as revoked."""
        token.revoked = True
        await self._session.flush()
