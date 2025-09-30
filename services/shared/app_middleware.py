from fastapi import FastAPI
from starlette.middleware import Middleware

from services.shared.middleware.cors import CORSMiddlewarePerTenant
from services.shared.middleware_utils import RequestIdMiddleware, TenantMiddleware

middlewares = [
    Middleware(TenantMiddleware),
    Middleware(CORSMiddlewarePerTenant),  # <- Adicionado aqui na ordem correta
]


def apply_middlewares(app: FastAPI) -> None:
    # Ordem importa: o ÚLTIMO adicionado roda primeiro (outermost).
    # Queremos Tenant rodando antes do CORS -> então adicionamos CORS antes.
    app.add_middleware(CORSMiddlewarePerTenant)  # inner
    app.add_middleware(TenantMiddleware)  # outer de CORS
    app.add_middleware(RequestIdMiddleware)
