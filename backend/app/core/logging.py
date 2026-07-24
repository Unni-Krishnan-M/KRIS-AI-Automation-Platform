"""Structured JSON logging configuration.

Every log line is a single JSON object on stdout, which container log
collectors and observability tooling can parse directly.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings


class JSONFormatter(logging.Formatter):
    """Render log records as compact JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attached by RequestIDMiddleware via LoggerAdapter / extra=...
        request_id = getattr(record, "request_id", None)
        if request_id is not None:
            payload["request_id"] = request_id

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Install the JSON formatter on the root logger.

    Idempotent: safe to call from both the app factory and the lifespan hook.
    """
    settings = get_settings()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level.upper())

    # Quiet noisy access logs; our middleware records structured request logs.
    logging.getLogger("uvicorn.access").handlers.clear()
