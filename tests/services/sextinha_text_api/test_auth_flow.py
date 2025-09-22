import pytest
from fastapi.testclient import TestClient

from services.sextinha_text_api.app.main import app
from services.shared import tenant_repo
from services.shared.tenant_context import TenantInfo

client = TestClient(app)


@pytest.fixture(autouse=True)
def stub_repo(monkeypatch):
    """Stub padrão: retorna tenants válidos; chaves desconhecidas -> None."""

    def fake_find(api_key: str):
        mapping = {
            "camila123": TenantInfo(
                id="1", name="Dra. Camila", api_key="camila123", status="active"
            ),
            "zeoficina456": TenantInfo(
                id="2", name="Oficina do Zé", api_key="zeoficina456", status="active"
            ),
            "squad789": TenantInfo(id="3", name="Squad Inc", api_key="squad789", status="active"),
        }
        return mapping.get(api_key)

    monkeypatch.setattr(tenant_repo, "find_tenant_by_api_key", fake_find)
    yield


def test_only_v1_requires_api_key():
    # rota pública continua livre
    r = client.post("/analyze", json={"text": "Sextinha é braba demais!"})
    assert r.status_code == 200

    # rota versionada exige header
    r = client.get("/v1/ping")
    assert r.status_code == 401


@pytest.mark.parametrize(
    "api_key,expect",
    [
        ("camila123", "Dra. Camila"),
        ("zeoficina456", "Oficina do Zé"),
        ("squad789", "Squad Inc"),
    ],
)
def test_v1_ping_valid_keys(api_key, expect):
    r = client.get("/v1/ping", headers={"x-api-key": api_key})
    assert r.status_code == 200
    assert expect in r.json()["message"]


def test_v1_ping_invalid_key_403():
    r = client.get("/v1/ping", headers={"x-api-key": "nope"})
    assert r.status_code == 403


def test_docs_and_openapi_are_public():
    r = client.get("/docs")
    assert r.status_code == 200
    r = client.get("/openapi.json")
    assert r.status_code == 200


def test_readiness_is_public():
    r = client.get("/readiness")
    assert r.status_code == 200


def test_openapi_applies_security_only_on_v1():
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    paths = spec.get("paths", {})

    # /v1/ping deve ter 'security'
    v1_ping = paths.get("/v1/ping", {}).get("get", {})
    assert "security" in v1_ping and v1_ping["security"], "security ausente em /v1/ping"

    # /analyze NÃO deve ter 'security'
    analyze = paths.get("/analyze", {}).get("post", {})
    assert "security" not in analyze, "/analyze não deveria exigir auth"


def test_repo_unavailable_returns_503(monkeypatch):
    # monkeypatch específico para este teste
    def raise_unavailable(_api_key: str):
        raise tenant_repo.TenantRepoUnavailable("down")

    monkeypatch.setattr(tenant_repo, "find_tenant_by_api_key", raise_unavailable)

    r = client.get("/v1/ping", headers={"x-api-key": "camila123"})
    assert r.status_code == 503
