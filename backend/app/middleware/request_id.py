"""Request-ID middleware.

Assigns every request a correlation ID (honouring an inbound ``X-Request-ID``
header if present), exposes it on ``request.state.request_id``, echoes it back
on the response, and emits a structured access log line.
"""

from __future__ import annotations

import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("kris.access")

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a correlation ID to each request/response and log it."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id

        logger.info(
            "%s %s -> %d",
            request.method,
            request.url.path,
            response.status_code,
            extra={"request_id": request_id},
        )
        return response
