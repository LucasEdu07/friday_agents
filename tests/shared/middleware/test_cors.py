# tests/shared/middleware/test_cors.py
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.testclient import TestClient
from starlette.types import ASGIApp

from services.shared.middleware.cors import CORSMiddlewarePerTenant


# 🔧 Middleware fake para simular o tenant resolvido antes do CORS
class FakeTenant:
    def __init__(self, config: dict):
        self.id = "test-tenant"
        self.name = "Test Tenant"
        self.config = config


class FakeTenantMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, tenant_config: dict):
        super().__init__(app)
        self.tenant_config = tenant_config

    async def dispatch(self, request: Request, call_next):
        tenant = FakeTenant(self.tenant_config)
        # setamos nos dois lugares que o CORS consulta
        request.state.tenant = tenant
        request.state.tenant_config = tenant.config
        return await call_next(request)


# 🧪 Cria app de teste com os middlewares simulados
def make_app(tenant_config: dict) -> TestClient:
    app = FastAPI()

    # IMPORTANTE: o último adicionado roda primeiro (outermost).
    # Queremos que o FakeTenant rode ANTES do CORS -> então adicionamos CORS antes.
    app.add_middleware(CORSMiddlewarePerTenant)
    app.add_middleware(FakeTenantMiddleware, tenant_config=tenant_config)

    @app.get("/v1/teste")
    def route():
        return {"ok": True}

    return TestClient(app)


def test_valid_origin_allows_request():
    client = make_app({"cors": {"origins": ["https://valido.com"]}})

    response = client.get("/v1/teste", headers={"Origin": "https://valido.com"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert response.headers["access-control-allow-origin"] == "https://valido.com"
    assert response.headers["vary"] == "Origin"


def test_invalid_origin_is_blocked():
    client = make_app({"cors": {"origins": ["https://valido.com"]}})

    response = client.get("/v1/teste", headers={"Origin": "https://malicioso.com"})

    assert response.status_code == 403
    assert response.json()["detail"] == "CORS origin não permitida"


def test_preflight_options_request_passes_for_valid_origin():
    client = make_app({"cors": {"origins": ["https://valido.com"]}})

    response = client.options(
        "/v1/teste",
        headers={
            "Origin": "https://valido.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Custom-Header",
        },
    )

    assert response.status_code == 204
    assert response.headers["access-control-allow-origin"] == "https://valido.com"
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers
