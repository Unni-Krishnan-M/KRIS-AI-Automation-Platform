"""Provider for the Ollama client (overridable in tests)."""

from __future__ import annotations

from app.core.config import get_settings
from app.services.ollama import OllamaClient


def get_ollama_client() -> OllamaClient:
    """FastAPI dependency returning a configured Ollama client."""
    return OllamaClient(get_settings())
