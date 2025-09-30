from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.testclient import TestClient
from starlette.types import ASGIApp

from services.shared.middleware.cors import CORSMiddlewarePerTenant


# 🔧 Middleware fake para simular o tenant resolvido antes
class FakeTenant:
    def __init__(self, config: dict):
        self.config = config


class FakeTenantMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, tenant_config: dict):
        super().__init__(app)
        self.tenant_config = tenant_config

    async def dispatch(self, request: Request, call_next):
        request.state.tenant = FakeTenant(self.tenant_config)
        return await call_next(request)


# 🧪 Cria app de teste com os middlewares simulados
def make_app(tenant_config: dict) -> TestClient:
    app = FastAPI()

    # registra CORS primeiro (interna)
    app.add_middleware(CORSMiddlewarePerTenant)
    # registra FakeTenant por último (externa) — ele será executado antes do CORS
    app.add_middleware(FakeTenantMiddleware, tenant_config=tenant_config)

    @app.get("/teste")
    def route():
        return {"ok": True}

    return TestClient(app)


def test_valid_origin_allows_request():
    client = make_app({"cors": {"origins": ["https://valido.com"]}})

    response = client.get("/teste", headers={"Origin": "https://valido.com"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert response.headers["access-control-allow-origin"] == "https://valido.com"
    assert response.headers["vary"] == "Origin"


def test_invalid_origin_is_blocked():
    client = make_app({"cors": {"origins": ["https://valido.com"]}})

    response = client.get("/teste", headers={"Origin": "https://malicioso.com"})

    assert response.status_code == 403
    assert response.json()["detail"] == "CORS origin não permitida"


def test_preflight_options_request_passes_for_valid_origin():
    client = make_app({"cors": {"origins": ["https://valido.com"]}})

    response = client.options(
        "/teste",
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
