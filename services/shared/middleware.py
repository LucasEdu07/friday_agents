from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from . import tenant_repo
from .tenant_context import set_current_tenant


class TenantMiddleware(BaseHTTPMiddleware):
    SAFE_PATHS = {"/", "/openapi.json", "/readiness", "/health"}
    SAFE_PREFIXES = ("/docs", "/redoc")
    PROTECTED_PREFIXES = ("/v1/",)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if (
            request.method == "OPTIONS"
            or path in self.SAFE_PATHS
            or any(path.startswith(p) for p in self.SAFE_PREFIXES)
            or not path.startswith(self.PROTECTED_PREFIXES)
        ):
            return await call_next(request)

        api_key = request.headers.get("x-api-key")
        if not api_key:
            return JSONResponse({"detail": "x-api-key is required"}, status_code=401)

        try:
            tenant = tenant_repo.find_tenant_by_api_key(api_key)
        except tenant_repo.TenantRepoUnavailable:
            return JSONResponse({"detail": "Tenant repository unavailable"}, status_code=503)

        if tenant is None:
            return JSONResponse({"detail": "Invalid API key"}, status_code=403)

        set_current_tenant(tenant)
        try:
            return await call_next(request)
        finally:
            set_current_tenant(None)
