"""Password hashing and JWT creation/verification.

Access tokens are short-lived bearer credentials. Refresh tokens are
long-lived, carry a unique ``jti`` so they can be tracked and revoked in the
database, and are rotated on every use.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
from jose import jwt

from app.core.config import get_settings

TokenType = Literal["access", "refresh"]

# bcrypt only hashes the first 72 bytes and newer versions raise on longer
# input, so passwords are truncated to 72 bytes before hashing/verifying.
_BCRYPT_MAX_BYTES = 72


def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(_encode(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    return bcrypt.checkpw(_encode(plain_password), hashed_password.encode("utf-8"))


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
) -> tuple[str, str, datetime]:
    """Return ``(encoded_jwt, jti, expires_at)``."""
    settings = get_settings()
    now = datetime.now(UTC)
    expires_at = now + expires_delta
    jti = str(uuid.uuid4())
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": expires_at,
        "jti": jti,
    }
    encoded = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded, jti, expires_at


def create_access_token(subject: str) -> str:
    """Create a short-lived access token for ``subject`` (the user id)."""
    settings = get_settings()
    token, _, _ = _create_token(
        subject,
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
    )
    return token


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    """Create a refresh token; returns ``(token, jti, expires_at)``."""
    settings = get_settings()
    return _create_token(
        subject,
        "refresh",
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT (raises ``jose.JWTError`` on failure)."""
    settings = get_settings()
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )
    return payload
