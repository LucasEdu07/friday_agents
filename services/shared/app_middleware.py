from fastapi import FastAPI

from services.shared.middleware.cors import CORSMiddlewarePerTenant
from services.shared.middleware.rate_limit import RateLimitMiddlewarePerTenant
from services.shared.middleware.request_logging import RequestLoggingMiddleware
from services.shared.middleware_utils import RequestIdMiddleware, TenantMiddleware


def apply_middlewares(app: FastAPI) -> None:
    """
    Ordem efetiva de execução (o ÚLTIMO adicionado roda primeiro):
      RequestLogging -> RequestId -> Tenant -> RateLimit -> CORS
    """
    app.add_middleware(CORSMiddlewarePerTenant)  # innermost
    app.add_middleware(RateLimitMiddlewarePerTenant)
    app.add_middleware(TenantMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(RequestLoggingMiddleware)  # outermost
