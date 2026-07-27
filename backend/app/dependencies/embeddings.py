"""Provider for the embedding client (overridable in tests)."""

from __future__ import annotations

from app.core.config import get_settings
from app.services.embeddings import EmbeddingClient


def get_embedding_client() -> EmbeddingClient:
    """FastAPI dependency returning a configured embedding client."""
    return EmbeddingClient(get_settings())
