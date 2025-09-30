import pytest
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.testclient import TestClient
from starlette.types import ASGIApp

import services.shared.middleware.rate_limit as rl
from services.shared.middleware.rate_limit import RateLimitMiddlewarePerTenant
from services.shared.middleware_utils import RequestIdMiddleware


class FakeTenant:
    def __init__(self, tid: str, config: dict):
        self.id = tid
        self.config = config


@pytest.fixture(autouse=True)
def clear_buckets():
    rl._BUCKETS.clear()


class FakeTenantMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, tenant_id: str, tenant_config: dict):
        super().__init__(app)
        self.tenant_id = tenant_id
        self.tenant_config = tenant_config

    async def dispatch(self, request: Request, call_next):
        request.state.tenant = FakeTenant(self.tenant_id, self.tenant_config)
        return await call_next(request)


def make_app(tenant_id: str, tenant_config: dict) -> TestClient:
    app = FastAPI()

    @app.get("/v1/ping")
    def ping():
        return {"ok": True}

    # Ordem: CORS (inner) <- RateLimit <- Tenant <- RequestId (outermost)
    # (CORS não é necessário nos testes de RL, então omitimos aqui)
    app.add_middleware(RateLimitMiddlewarePerTenant)  # inner
    app.add_middleware(
        FakeTenantMiddleware, tenant_id=tenant_id, tenant_config=tenant_config
    )  # middle
    app.add_middleware(RequestIdMiddleware)  # outermost

    return TestClient(app)


def test_within_limit_passes():
    cfg = {"rate_limit": {"default": {"rpm": 5, "burst": 5}}}
    c = make_app("T1", cfg)
    for _ in range(5):
        r = c.get("/v1/ping")
        assert r.status_code == 200


def test_exceed_limit_returns_429():
    cfg = {"rate_limit": {"default": {"rpm": 2, "burst": 2}}}
    c = make_app("T1", cfg)
    assert c.get("/v1/ping").status_code == 200
    assert c.get("/v1/ping").status_code == 200
    r = c.get("/v1/ping")  # 3ª dentro da janela
    assert r.status_code == 429
    body = r.json()
    assert body["detail"] == "Too Many Requests"
    assert body["tenant"] == "T1"


def test_distinct_limits_per_tenant_and_route():
    cfg_t1 = {"rate_limit": {"routes": {"/v1/ping": {"rpm": 1, "burst": 1}}}}
    cfg_t2 = {"rate_limit": {"routes": {"/v1/ping": {"rpm": 3, "burst": 3}}}}

    c1 = make_app("A", cfg_t1)
    c2 = make_app("B", cfg_t2)

    # T1 estoura na segunda
    assert c1.get("/v1/ping").status_code == 200
    assert c1.get("/v1/ping").status_code == 429

    # T2 consegue 3 dentro da janela
    assert c2.get("/v1/ping").status_code == 200
    assert c2.get("/v1/ping").status_code == 200
    assert c2.get("/v1/ping").status_code == 200
