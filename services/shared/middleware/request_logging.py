from __future__ import annotations

import time
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from services.shared.logging_utils import get_logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    # docstring igual...

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.base_logger = get_logger("access")

    def _context(self, request: Request) -> dict[str, Any]:
        rid = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")
        tenant = getattr(getattr(request.state, "tenant", None), "id", None)
        return {
            "request_id": rid,
            "tenant_id": tenant,
            "path": request.url.path,
            "method": request.method,
        }

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        ctx = self._context(request)
        # opcional: log de início
        # get_logger("access", ctx).debug("request.start")

        try:
            response: Response = await call_next(request)
            status = response.status_code
        except Exception:
            duration_ms = int((time.perf_counter() - start) * 1000)
            get_logger("access", {**ctx, "status": 500, "duration_ms": duration_ms}).exception(
                "request.error"
            )
            raise
        else:
            duration_ms = int((time.perf_counter() - start) * 1000)
            get_logger("access", {**ctx, "status": status, "duration_ms": duration_ms}).info(
                "request.end"
            )
            return response
