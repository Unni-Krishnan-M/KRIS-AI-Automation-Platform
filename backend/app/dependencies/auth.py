"""Authentication dependencies: resolve the current user from a bearer token."""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository

_bearer = HTTPBearer()

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Validate the access token and return the authenticated user."""
    try:
        payload = decode_token(credentials.credentials)
    except JWTError as exc:
        raise _credentials_exception from exc

    if payload.get("type") != "access":
        raise _credentials_exception

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise _credentials_exception

    try:
        user_id = uuid.UUID(subject)
    except ValueError as exc:
        raise _credentials_exception from exc

    user = await UserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise _credentials_exception
    return user
