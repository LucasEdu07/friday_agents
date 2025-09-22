# no topo do arquivo:
import uuid

from fastapi.testclient import TestClient

from services.sextinha_vision_api.app.main import app

client = TestClient(app)

# 👇 Quebra o base64 em duas partes para não estourar 100 colunas.
IMG_1X1_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9oQJm1cA"
    "AAAASUVORK5CYII="
)


def test_health_generates_request_id():
    r = client.get("/health")
    assert r.status_code in (200, 204)
    rid = r.headers.get("X-Request-Id")
    assert rid
    uuid.UUID(rid)  # valida formato UUID


def test_v1_analyze_unauth_has_request_id():
    payload = {"image_base64": IMG_1X1_PNG_B64}
    r = client.post("/v1/vision/analyze", json=payload)
    assert r.status_code == 401
    assert r.headers.get("X-Request-Id")


def test_v1_analyze_auth_propagates_request_id_and_sets_tenant():
    payload = {"image_base64": IMG_1X1_PNG_B64}
    rid = "3c3c3ad3-0d8e-4f7d-8b1e-f45d9f6b9a11"
    r = client.post(
        "/v1/vision/analyze",
        json=payload,
        headers={"X-Api-Key": "seed-acme-key", "X-Request-Id": rid},
    )
    # sempre deve ecoar o RID
    assert r.headers.get("X-Request-Id") == rid
    if r.status_code == 200:
        assert r.headers.get("X-Tenant-Id")
