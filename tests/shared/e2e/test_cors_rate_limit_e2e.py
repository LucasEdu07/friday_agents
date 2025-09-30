from __future__ import annotations

import pytest
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.testclient import TestClient
from starlette.types import ASGIApp

import services.shared.middleware.rate_limit as rl
from services.shared.middleware.cors import CORSMiddlewarePerTenant
from services.shared.middleware.rate_limit import (
    RateLimitMiddlewarePerTenant,
)
from services.shared.middleware_utils import RequestIdMiddleware

# ---- Fixtures utilitárias ----------------------------------------------------


@pytest.fixture(autouse=True)
def clear_rate_limit_buckets():
    """Isola os testes limpando os baldes de rate limit entre cenários."""
    rl._BUCKETS.clear()  # noqa: SLF001  (acesso interno controlado só p/ teste)
    yield
    rl._BUCKETS.clear()


class FakeTenant:
    def __init__(self, tid: str, name: str, config: dict):
        self.id = tid
        self.name = name
        self.config = config


class FakeTenantMiddleware(BaseHTTPMiddleware):
    """Simula o TenantMiddleware: injeta tenant e config no request.state."""

    def __init__(self, app: ASGIApp, tenant_id: str, tenant_config: dict):
        super().__init__(app)
        self.tenant_id = tenant_id
        self.tenant_config = tenant_config

    async def dispatch(self, request: Request, call_next):
        tenant = FakeTenant(self.tenant_id, "E2E Tenant", self.tenant_config)
        request.state.tenant = tenant
        request.state.tenant_config = tenant.config
        return await call_next(request)


def make_app(tenant_id: str, tenant_config: dict) -> TestClient:
    """Monta um app FastAPI com a ordem real dos middlewares.

    Ordem (o último adicionado é o primeiro a rodar):
      RequestId (outermost) -> FakeTenant -> RateLimit -> CORS (innermost)
    """
    app = FastAPI()

    # rota versionada (CORS por tenant só aplica em /v1/*)
    @app.get("/v1/teste")
    def route():
        return {"ok": True}

    # stack
    app.add_middleware(CORSMiddlewarePerTenant)  # innermost
    app.add_middleware(RateLimitMiddlewarePerTenant)  # entre tenant e CORS
    app.add_middleware(FakeTenantMiddleware, tenant_id=tenant_id, tenant_config=tenant_config)
    app.add_middleware(RequestIdMiddleware)  # outermost

    return TestClient(app)


# ---- CORS --------------------------------------------------------------------


def test_cors_valid_origin_allows_request():
    cfg = {"cors": {"origins": ["https://valido.com"]}}
    client = make_app("T1", cfg)

    r = client.get("/v1/teste", headers={"Origin": "https://valido.com"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}

    hl = {k.lower(): v for k, v in r.headers.items()}
    assert hl.get("access-control-allow-origin") == "https://valido.com"
    assert hl.get("vary") == "Origin"


def test_cors_invalid_origin_is_blocked():
    cfg = {"cors": {"origins": ["https://valido.com"]}}
    client = make_app("T1", cfg)

    r = client.get("/v1/teste", headers={"Origin": "https://malicioso.com"})
    assert r.status_code == 403
    body = r.json()
    assert body.get("detail") == "CORS origin não permitida"


def test_cors_preflight_options_passes_for_valid_origin():
    cfg = {"cors": {"origins": ["https://valido.com"]}}
    client = make_app("T1", cfg)

    r = client.options(
        "/v1/teste",
        headers={
            "Origin": "https://valido.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Custom-Header",
        },
    )
    assert r.status_code == 204
    hl = {k.lower(): v for k, v in r.headers.items()}
    assert hl.get("access-control-allow-origin") == "https://valido.com"
    assert "access-control-allow-methods" in hl
    assert "access-control-allow-headers" in hl


# ---- Rate limit --------------------------------------------------------------


def test_rate_limit_within_limit_then_429():
    cfg = {
        "cors": {"origins": ["https://valido.com"]},
        "rate_limit": {"routes": {"/v1/teste": {"rpm": 2, "burst": 2}}},
    }
    client = make_app("T1", cfg)

    assert client.get("/v1/teste").status_code == 200
    assert client.get("/v1/teste").status_code == 200
    r3 = client.get("/v1/teste")
    assert r3.status_code == 429
    assert r3.json() == {"detail": "Too Many Requests", "tenant": "T1"}


def test_rate_limit_isolated_across_tenants():
    cfg_t1 = {"rate_limit": {"routes": {"/v1/teste": {"rpm": 1, "burst": 1}}}}
    cfg_t2 = {"rate_limit": {"routes": {"/v1/teste": {"rpm": 3, "burst": 3}}}}

    c1 = make_app("A", cfg_t1)
    c2 = make_app("B", cfg_t2)

    # T1 estoura na 2ª
    assert c1.get("/v1/teste").status_code == 200
    assert c1.get("/v1/teste").status_code == 429

    # T2 aguenta 3
    assert c2.get("/v1/teste").status_code == 200
    assert c2.get("/v1/teste").status_code == 200
    assert c2.get("/v1/teste").status_code == 200
