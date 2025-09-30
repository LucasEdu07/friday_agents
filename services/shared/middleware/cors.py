# services/shared/middleware/cors.py
from typing import cast

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp


class CORSMiddlewarePerTenant(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        tenant = getattr(request.state, "tenant", None)
        if tenant is None:
            return JSONResponse({"detail": "Tenant não resolvido"}, status_code=400)

        tenant_config = getattr(tenant, "config", None)
        if not tenant_config:
            return JSONResponse({"detail": "Tenant config não disponível"}, status_code=400)

        allowed_origins = tenant_config.get("cors", {}).get("origins", [])
        origin = request.headers.get("origin")

        # Se houver Origin e ela não é permitida -> 403
        if origin and origin not in allowed_origins:
            return JSONResponse({"detail": "CORS origin não permitida"}, status_code=403)

        # Preflight
        if request.method == "OPTIONS" and origin in allowed_origins:
            # aqui origin não é None, mas mypy não infere — explicitamos:
            assert origin is not None
            acrh = request.headers.get("access-control-request-headers") or "*"
            headers: dict[str, str] = {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": acrh,
            }
            return Response(status_code=204, headers=headers)

        # Requisição normal
        response: Response = await call_next(request)
        if origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = cast(str, origin)
            response.headers["Vary"] = "Origin"
        return response
