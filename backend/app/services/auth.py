"""Authentication business logic.

Orchestrates the user and refresh-token repositories and the security helpers.
Raises :class:`~app.core.exceptions.AppError` for expected failures (mapped to
HTTP status codes by the global handler).
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse

_INVALID_CREDENTIALS = "Invalid email or password"
_INVALID_TOKEN = "Invalid or expired refresh token"  # noqa: S105 - error message, not a secret


class AuthService:
    """Registration, login, token refresh, and logout."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._tokens = RefreshTokenRepository(session)

    async def register(self, email: str, password: str, full_name: str | None) -> User:
        """Create a new user; fails if the email is already registered."""
        if await self._users.get_by_email(email) is not None:
            raise AppError("Email already registered", status.HTTP_409_CONFLICT)

        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
        )
        await self._users.create(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User:
        """Return the user if the credentials are valid, else raise."""
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise AppError(_INVALID_CREDENTIALS, status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            raise AppError("User account is inactive", status.HTTP_403_FORBIDDEN)
        return user

    async def login(self, email: str, password: str) -> TokenResponse:
        """Authenticate and issue a new token pair."""
        user = await self.authenticate(email, password)
        return await self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Rotate a valid refresh token for a new access/refresh pair."""
        payload = self._decode_refresh(refresh_token)

        jti = payload.get("jti")
        stored = await self._tokens.get_by_jti(jti) if jti else None
        if stored is None or stored.revoked:
            raise AppError(_INVALID_TOKEN, status.HTTP_401_UNAUTHORIZED)

        user = await self._users.get_by_id(uuid.UUID(payload["sub"]))
        if user is None or not user.is_active:
            raise AppError(_INVALID_TOKEN, status.HTTP_401_UNAUTHORIZED)

        # Rotate: revoke the used token before issuing a new pair.
        await self._tokens.revoke(stored)
        return await self._issue_tokens(user)

    async def logout(self, refresh_token: str) -> None:
        """Revoke a refresh token (idempotent; unknown tokens are ignored)."""
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            return
        jti = payload.get("jti")
        if not jti:
            return
        stored = await self._tokens.get_by_jti(jti)
        if stored is not None and not stored.revoked:
            await self._tokens.revoke(stored)
            await self._session.commit()

    async def _issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(str(user.id))
        refresh_token, jti, expires_at = create_refresh_token(str(user.id))
        await self._tokens.create(user.id, jti, expires_at)
        await self._session.commit()
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    def _decode_refresh(self, refresh_token: str) -> dict[str, Any]:
        try:
            payload = decode_token(refresh_token)
        except JWTError as exc:
            raise AppError(_INVALID_TOKEN, status.HTTP_401_UNAUTHORIZED) from exc
        if payload.get("type") != "refresh" or "sub" not in payload:
            raise AppError(_INVALID_TOKEN, status.HTTP_401_UNAUTHORIZED)
        return payload
