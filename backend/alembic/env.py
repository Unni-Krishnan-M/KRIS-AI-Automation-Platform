"""Alembic migration environment.

Migrations run through the *synchronous* driver (``DATABASE_SYNC_URL``) — the
async engine is for the application; Alembic is simpler and more robust with a
sync connection. The URL comes from application settings and is passed straight
to the engine, bypassing the ini file (whose ``%`` interpolation would corrupt
URL-encoded passwords such as ``%40``).
"""

from __future__ import annotations

from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context
from app.core.config import get_settings
from app.db.base import Base
from app.models import User  # noqa: F401 - registers models on Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

DB_URL = get_settings().database_sync_url
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL without a live DB connection (``alembic upgrade --sql``)."""
    context.configure(
        url=DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = create_engine(DB_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
