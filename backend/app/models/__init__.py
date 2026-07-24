"""ORM models package.

Importing every model here ensures they are registered on ``Base.metadata``
before Alembic autogenerate / ``create_all`` inspects it.
"""

from __future__ import annotations

from app.models.api_key import ApiKey
from app.models.refresh_token import RefreshToken
from app.models.user import User

__all__ = ["ApiKey", "RefreshToken", "User"]
