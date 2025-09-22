from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# importe o módulo para facilitar monkeypatch nos testes
from . import tenant_repo
from .tenant_context import set_current_tenant


class TenantMiddleware(BaseHTTPMiddleware):
    # rotas públicas
    SAFE_PATHS = {"/", "/openapi.json", "/readiness", "/health"}
    SAFE_PREFIXES = ("/docs", "/redoc")  # swagger e redoc

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 1) Libera docs/health e preflight
        if (
            request.method == "OPTIONS"
            or path in self.SAFE_PATHS
            or any(path.startswith(p) for p in self.SAFE_PREFIXES)
        ):
            return await call_next(request)

        # 2) Só protege rotas versionadas
        protected = path.startswith("/v1/")
        if not protected:
            return await call_next(request)

        # 3) Exige x-api-key
        api_key = request.headers.get("x-api-key")
        if not api_key:
            return JSONResponse({"detail": "x-api-key is required"}, status_code=401)

        # 4) Resolve tenant (tratando indisponibilidade do repo)
        try:
            tenant = tenant_repo.find_tenant_by_api_key(api_key)
        except tenant_repo.TenantRepoUnavailable:
            return JSONResponse({"detail": "Tenant repository unavailable"}, status_code=503)

        if tenant is None:
            return JSONResponse({"detail": "Invalid API key"}, status_code=403)

        # 5) Injeta contexto e segue
        set_current_tenant(tenant)
        try:
            return await call_next(request)
        finally:
            set_current_tenant(None)
