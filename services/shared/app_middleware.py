from fastapi import FastAPI
from starlette.middleware import Middleware

from services.shared.middleware.cors import CORSMiddlewarePerTenant
from services.shared.middleware.rate_limit import RateLimitMiddlewarePerTenant
from services.shared.middleware_utils import RequestIdMiddleware, TenantMiddleware

middlewares = [
    Middleware(TenantMiddleware),
    Middleware(CORSMiddlewarePerTenant),  # <- Adicionado aqui na ordem correta
]


def apply_middlewares(app: FastAPI) -> None:
    # Ordem importa (o último adicionado roda primeiro):
    # Queremos: RequestId (outermost) -> Tenant -> RateLimit -> CORS (innermost)
    app.add_middleware(CORSMiddlewarePerTenant)  # inner
    app.add_middleware(RateLimitMiddlewarePerTenant)  # entre tenant e CORS
    app.add_middleware(TenantMiddleware)  # middle
    app.add_middleware(RequestIdMiddleware)
