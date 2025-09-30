from __future__ import annotations

import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

# Token bucket simples por chave (memória local)
# key -> (tokens, last_ts, capacity, refill_per_sec)
_BUCKETS: dict[str, tuple[float, float, float, float]] = {}


def _now() -> float:
    return time.monotonic()


def _rule_for(request: Request) -> tuple[int, int]:
    """
    Retorna (rpm, burst) a aplicar para o tenant/rota atual.
    Fallback para default.rpm e default.burst (burst opcional).
    """
    tenant = getattr(request.state, "tenant", None)
    tenant_config = getattr(tenant, "config", {}) if tenant else {}

    cfg = tenant_config.get("rate_limit", {}) or {}
    dflt = cfg.get("default", {}) or {}
    routes = cfg.get("routes", {}) or {}

    path = request.url.path
    route_cfg = routes.get(path, {}) or {}

    rpm = int(route_cfg.get("rpm", dflt.get("rpm", 60)))
    burst = int(route_cfg.get("burst", dflt.get("burst", rpm)))  # burst default = rpm

    rpm = max(1, rpm)
    burst = max(1, burst)
    return rpm, burst


class RateLimitMiddlewarePerTenant(BaseHTTPMiddleware):
    """
    Rate limit por tenant + rota usando token bucket em memória.
    Chave: f"{tenant_id}:{path}". Retorna 429 ao exceder.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        tenant = getattr(request.state, "tenant", None)

        # Só aplicamos rate limit em rotas versionadas (/v1/*) e com tenant resolvido
        if not tenant or not request.url.path.startswith("/v1/"):
            return await call_next(request)

        tenant_id = getattr(tenant, "id", "unknown")
        path = request.url.path

        rpm, burst = _rule_for(request)
        refill_per_sec = rpm / 60.0
        capacity = float(max(burst, rpm))

        key = f"{tenant_id}:{path}"
        now = _now()

        tokens, last_ts, cap, rps = _BUCKETS.get(key, (capacity, now, capacity, refill_per_sec))

        # Refill
        elapsed = max(0.0, now - last_ts)
        tokens = min(capacity, tokens + elapsed * refill_per_sec)

        if tokens < 1.0:
            return JSONResponse(
                {"detail": "Too Many Requests", "tenant": str(tenant_id)},
                status_code=429,
            )

        # Consome 1 token e persiste
        tokens -= 1.0
        _BUCKETS[key] = (tokens, now, capacity, refill_per_sec)

        response: Response = await call_next(request)
        return response
