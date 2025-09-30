# services/shared/middleware/cors.py

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp


class CORSMiddlewarePerTenant(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 1) Fora de /v1 -> não aplica CORS por tenant
        if not path.startswith("/v1/"):
            return await call_next(request)

        # 2) Se não há tenant (rota aberta / erro a montante) -> não bloqueia aqui
        tenant = getattr(request.state, "tenant", None)
        if tenant is None:
            return await call_next(request)

        # 3) Lê allowed_origins do config do tenant (preferindo tenant_config se existir)
        tenant_config = getattr(request.state, "tenant_config", None) or getattr(
            tenant, "config", None
        )
        if not isinstance(tenant_config, dict):
            return JSONResponse({"detail": "Tenant config não disponível"}, status_code=400)

        allowed_origins = tenant_config.get("cors", {}).get("origins", []) or []
        origin = request.headers.get("origin")

        # 4) Bloqueia origin inválida apenas em /v1 (com tenant presente)
        if origin and origin not in allowed_origins:
            return JSONResponse({"detail": "CORS origin não permitida"}, status_code=403)

        # 5) Preflight
        if request.method == "OPTIONS" and origin in allowed_origins:
            acrh = request.headers.get("access-control-request-headers") or "*"

            assert origin is not None
            headers: dict[str, str] = {
                "Access-Control-Allow-Origin": origin or "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": acrh,
            }
            return Response(status_code=204, headers=headers)

        # 6) Resposta normal
        response: Response = await call_next(request)
        if origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
        return response
