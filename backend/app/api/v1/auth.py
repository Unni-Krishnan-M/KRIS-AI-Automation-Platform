"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserRead
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> User:
    """Create a new user account."""
    return await AuthService(session).register(payload.email, payload.password, payload.full_name)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Exchange credentials for an access/refresh token pair."""
    return await AuthService(session).login(payload.email, payload.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Rotate a refresh token for a new token pair."""
    return await AuthService(session).refresh(payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_db),
) -> None:
    """Revoke a refresh token."""
    await AuthService(session).logout(payload.refresh_token)


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user."""
    return current_user
