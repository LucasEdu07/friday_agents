import base64

from fastapi.testclient import TestClient

from services.sextinha_vision_api.app.main import app

client = TestClient(app)


def test_vision_analyze_ok():
    raw = b"hello vision"
    b64 = base64.b64encode(raw).decode()
    resp = client.post("/vision/analyze", json={"image_base64": b64})
    assert resp.status_code == 200
    data = resp.json()
    assert data["size_bytes"] == len(raw)
    assert data["format"] == "unknown"


def test_vision_analyze_invalid_b64():
    resp = client.post("/vision/analyze", json={"image_base64": "###"})
    assert resp.status_code in (400, 422)
