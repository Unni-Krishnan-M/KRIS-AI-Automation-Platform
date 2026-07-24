"""Application configuration loaded from environment variables.

All settings come from the environment (or a local ``.env`` file). No secret
has a default value — the app fails fast at startup if one is missing.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings.

    Field names map to UPPER_CASE environment variables (case-insensitive),
    e.g. ``database_url`` <- ``DATABASE_URL``.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────
    app_name: str = "KRIS"
    app_env: Literal["development", "staging", "production"] = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    # ── Database ─────────────────────────────────────────
    database_url: str
    database_sync_url: str

    # ── Redis ────────────────────────────────────────────
    redis_url: str

    # ── Ollama ───────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.1:8b"
    ollama_vision_model: str = "llama3.2-vision"
    ollama_embed_model: str = "nomic-embed-text"
    embed_dim: int = 768

    # ── Auth (no defaults for secrets) ───────────────────
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ── n8n ──────────────────────────────────────────────
    n8n_base_url: str = "http://localhost:5678"


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance.

    Cached so the environment is parsed once per process. Tests can reset the
    cache via ``get_settings.cache_clear()``.
    """
    return Settings()  # values supplied by the environment
