from fastapi.testclient import TestClient
from services.sextinha_vision_api.app.main import app

client = TestClient(app)

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "sextinha_vision_api"
