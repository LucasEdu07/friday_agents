from __future__ import annotations

import uuid
from typing import Final

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from . import tenant_repo
from .config_loader import load_config
from .tenant_context import TenantInfo, set_current_tenant

REQUEST_ID_HEADER: Final[str] = "X-Request-Id"
TENANT_ID_HEADER: Final[str] = "X-Tenant-Id"


def _looks_like_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except Exception:
        return False


def _ensure_request_id(request: Request) -> str:
    req_id = request.headers.get(REQUEST_ID_HEADER)
    if not req_id or not _looks_like_uuid(req_id):
        req_id = str(uuid.uuid4())
    request.state.request_id = req_id
    return req_id


def _to_tenant_info(tenant_obj: object) -> TenantInfo:
    def pick(*names: str) -> str | None:
        for n in names:
            if hasattr(tenant_obj, n):
                v = getattr(tenant_obj, n)
                if v:
                    return str(v)
        if isinstance(tenant_obj, dict):
            for n in names:
                v = tenant_obj.get(n)
                if v:
                    return str(v)
        return None

    tid = pick("tenant_id", "id")
    name = pick("name")
    api_key = pick("api_key", "key") or ""
    status = pick("status") or "active"

    if not tid:
        tid = name or "unknown"

    display_name = name or tid

    return TenantInfo(
        id=str(tid),
        name=str(display_name),
        api_key=str(api_key),
        status=str(status),
    )


def _attach_headers(
    response: Response,
    *,
    request_id: str,
    tenant_id: str | None = None,
) -> Response:
    response.headers[REQUEST_ID_HEADER] = request_id
    if tenant_id:
        response.headers[TENANT_ID_HEADER] = tenant_id
    return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    - Gera/propaga X-Request-Id para todas as requisições.
    - Injeta X-Request-Id em TODAS as respostas (incluindo 4xx/5xx).
    """

    async def dispatch(self, request: Request, call_next):
        req_id = _ensure_request_id(request)
        response: Response = await call_next(request)
        return _attach_headers(response, request_id=req_id)


class TenantMiddleware(BaseHTTPMiddleware):
    SAFE_PATHS = {"/", "/openapi.json", "/readiness", "/health", "/healthz"}
    SAFE_PREFIXES = ("/docs", "/redoc", "/static")
    OPEN_V1: set[str] = set()

    async def dispatch(self, request: Request, call_next):
        req_id = _ensure_request_id(request)
        path = request.url.path

        def respond(status: int, payload: dict) -> Response:
            resp = JSONResponse(payload, status_code=status)
            return _attach_headers(resp, request_id=req_id)

        if (
            request.method == "OPTIONS"
            or path in self.SAFE_PATHS
            or any(path.startswith(p) for p in self.SAFE_PREFIXES)
        ):
            resp = await call_next(request)
            return _attach_headers(resp, request_id=req_id)

        if not path.startswith("/v1/") or path in self.OPEN_V1:
            resp = await call_next(request)
            return _attach_headers(resp, request_id=req_id)

        api_key = request.headers.get("x-api-key")
        if not api_key:
            return respond(401, {"detail": "x-api-key is required"})

        try:
            tenant_row = tenant_repo.find_tenant_by_api_key(api_key)
        except tenant_repo.TenantRepoUnavailable:
            return respond(503, {"detail": "Tenant repository unavailable"})

        if tenant_row is None:
            return respond(403, {"detail": "Invalid API key"})

        tenant_info = _to_tenant_info(tenant_row)

        try:
            config = load_config(tenant_info.id)
        except FileNotFoundError:
            try:
                from .config_provisioner import sync_from_db

                sync_from_db(overwrite=False)
                config = load_config(tenant_info.id)
            except Exception:
                return respond(503, {"detail": "Tenant config not available"})

        request.state.tenant = tenant_info
        request.state.tenant_config = config
        set_current_tenant(tenant_info)

        try:
            response: Response = await call_next(request)
        finally:
            set_current_tenant(None)

        return _attach_headers(response, request_id=req_id, tenant_id=tenant_info.id)
