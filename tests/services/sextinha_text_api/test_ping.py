import pytest
from fastapi.testclient import TestClient

from services.sextinha_text_api.app.main import app
from services.shared import tenant_repo
from services.shared.tenant_context import TenantInfo


@pytest.fixture(autouse=True)
def stub_tenant_repo(monkeypatch):
    def fake_find(api_key: str):
        if api_key == "camila123":
            return TenantInfo(id="1", name="Dra. Camila", api_key=api_key, status="active")
        if api_key == "zeoficina456":
            return TenantInfo(id="2", name="Oficina do Zé", api_key=api_key, status="active")
        return None

    monkeypatch.setattr(tenant_repo, "find_tenant_by_api_key", fake_find)
    yield


client = TestClient(app)


def test_ping_camila_ok():
    r = client.get("/v1/ping", headers={"x-api-key": "camila123"})
    assert r.status_code == 200
    assert r.json()["message"].endswith("Dra. Camila")


def test_ping_ze_ok():
    r = client.get("/v1/ping", headers={"x-api-key": "zeoficina456"})
    assert r.status_code == 200
    assert r.json()["message"].endswith("Oficina do Zé")


def test_ping_missing_key_401():
    r = client.get("/v1/ping")
    assert r.status_code == 401


def test_ping_invalid_key_403():
    r = client.get("/v1/ping", headers={"x-api-key": "invalida"})
    assert r.status_code == 403


def test_docs_and_readiness_open():
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/readiness").status_code == 200
