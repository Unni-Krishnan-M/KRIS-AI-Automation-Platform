"""Async client for Ollama text embeddings (nomic-embed-text)."""

from __future__ import annotations

import httpx

from app.core.config import Settings

_TIMEOUT = httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0)


class EmbeddingClient:
    """Generates embedding vectors via Ollama's ``/api/embeddings`` endpoint."""

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_embed_model
        self.dim = settings.embed_dim

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""
        vectors: list[list[float]] = []
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            for text in texts:
                response = await client.post(
                    f"{self._base_url}/api/embeddings",
                    json={"model": self._model, "prompt": text},
                )
                response.raise_for_status()
                vectors.append(response.json()["embedding"])
        return vectors

    async def embed_query(self, text: str) -> list[float]:
        """Return the embedding vector for a single query string."""
        vectors = await self.embed_texts([text])
        return vectors[0]
