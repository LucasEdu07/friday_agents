# services/shared/middleware.py
from __future__ import annotations

import uuid
from typing import Final

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

# importe o módulo para facilitar monkeypatch nos testes
from . import tenant_repo
from .tenant_context import set_current_tenant

# ===============================
# Constantes / helpers
# ===============================

REQUEST_ID_HEADER: Final[str] = "X-Request-Id"
TENANT_ID_HEADER: Final[str] = "X-Tenant-Id"


def _looks_like_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except Exception:
        return False


def _ensure_request_id(request: Request) -> str:
    """Obtém (ou gera) um Request ID e grava em request.state.request_id."""
    req_id = request.headers.get(REQUEST_ID_HEADER)
    if not req_id or not _looks_like_uuid(req_id):
        req_id = str(uuid.uuid4())
    request.state.request_id = req_id
    return req_id


def _extract_tenant_id(tenant_obj: object | None) -> str | None:
    """Extrai uma string representando o tenant_id do objeto resolvido."""
    if tenant_obj is None:
        return None
    for attr in ("tenant_id", "id", "slug", "name"):
        if hasattr(tenant_obj, attr):
            v = getattr(tenant_obj, attr)
            if v:
                return str(v)
    # último recurso: repr
    return str(tenant_obj)


def _attach_headers(
    response: Response,
    *,
    request_id: str,
    tenant_id: str | None = None,
) -> Response:
    """Garante cabeçalhos comuns em qualquer Response."""
    response.headers[REQUEST_ID_HEADER] = request_id
    if tenant_id:
        response.headers[TENANT_ID_HEADER] = tenant_id
    return response


# ===============================
# RequestIdMiddleware
# ===============================


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    - Gera/propaga X-Request-Id para todas as requisições.
    - Injeta X-Request-Id em TODAS as respostas (incluindo 4xx/5xx).
    """

    async def dispatch(self, request: Request, call_next):
        req_id = _ensure_request_id(request)

        # segue o fluxo normal
        response: Response = await call_next(request)

        # sempre anexa o header ao final
        return _attach_headers(response, request_id=req_id)


# ===============================
# TenantMiddleware
# ===============================


class TenantMiddleware(BaseHTTPMiddleware):
    """
    - Protege apenas rotas '/v1/*' exigindo 'x-api-key'.
    - Resolve tenant via tenant_repo, injeta contexto e 'request.state.tenant'.
    - Sempre anexa 'X-Request-Id' e, quando houver tenant, 'X-Tenant-Id' na resposta.
    - Cobre respostas de curto-circuito (401/403/503) com headers.
    """

    # rotas públicas
    SAFE_PATHS = {"/", "/openapi.json", "/readiness", "/health"}
    SAFE_PREFIXES = ("/docs", "/redoc")  # swagger/redoc

    async def dispatch(self, request: Request, call_next):
        # Fallback robusto de X-Request-Id para QUALQUER saída desta middleware
        req_id = _ensure_request_id(request)

        path = request.url.path

        def _respond(status: int, payload: dict) -> Response:
            return _attach_headers(
                JSONResponse(payload, status_code=status),
                request_id=req_id,
            )

        # 1) Libera docs/health e preflight
        if (
            request.method == "OPTIONS"
            or path in self.SAFE_PATHS
            or any(path.startswith(p) for p in self.SAFE_PREFIXES)
        ):
            resp = await call_next(request)
            # pode já existir tenant em algum fluxo anterior; propaga se houver
            tid = _extract_tenant_id(getattr(request.state, "tenant", None))
            return _attach_headers(resp, request_id=req_id, tenant_id=tid)

        # 2) Protege apenas /v1/*
        if not path.startswith("/v1/"):
            resp = await call_next(request)
            tid = _extract_tenant_id(getattr(request.state, "tenant", None))
            return _attach_headers(resp, request_id=req_id, tenant_id=tid)

        # 3) Exige x-api-key
        api_key = request.headers.get("x-api-key")
        if not api_key:
            return _respond(401, {"detail": "x-api-key is required"})

        # 4) Resolve tenant (tratando indisponibilidade do repo)
        try:
            tenant = tenant_repo.find_tenant_by_api_key(api_key)
        except tenant_repo.TenantRepoUnavailable:
            return _respond(503, {"detail": "Tenant repository unavailable"})

        if tenant is None:
            return _respond(403, {"detail": "Invalid API key"})

        # 5) Injeta contexto e segue
        set_current_tenant(tenant)
        request.state.tenant = tenant  # disponível a jusante

        try:
            response: Response = await call_next(request)
        finally:
            set_current_tenant(None)

        # 6) Sempre anexa headers ao final
        tid = _extract_tenant_id(tenant)
        return _attach_headers(response, request_id=req_id, tenant_id=tid)
