"""Async client for the Ollama model server.

Wraps Ollama's ``/api/chat`` endpoint. ``chat_stream`` yields assistant text
deltas as they arrive (newline-delimited JSON from Ollama).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from app.core.config import Settings

# Generous read timeout: local model generation can take a while; fail fast on
# connect so a down server surfaces immediately.
_TIMEOUT = httpx.Timeout(connect=5.0, read=300.0, write=30.0, pool=5.0)


class OllamaClient:
    """Thin async wrapper over the Ollama chat API."""

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._default_model = settings.ollama_chat_model

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream assistant text deltas for the given message history."""
        payload = {
            "model": model or self._default_model,
            "messages": messages,
            "stream": True,
        }
        async with (
            httpx.AsyncClient(timeout=_TIMEOUT) as client,
            client.stream("POST", f"{self._base_url}/api/chat", json=payload) as response,
        ):
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                data = json.loads(line)
                chunk = data.get("message", {}).get("content", "")
                if chunk:
                    yield chunk
                if data.get("done"):
                    break
