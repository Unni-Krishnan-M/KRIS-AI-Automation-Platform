"""Authentication request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Payload for creating a new account."""

    email: EmailStr
    # bcrypt only considers the first 72 bytes, so cap the length there.
    password: str = Field(min_length=8, max_length=72)
    full_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    """Payload for exchanging credentials for tokens."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class RefreshRequest(BaseModel):
    """Payload carrying a refresh token."""

    refresh_token: str


class TokenResponse(BaseModel):
    """A freshly issued access/refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 - not a secret, the OAuth2 scheme name
