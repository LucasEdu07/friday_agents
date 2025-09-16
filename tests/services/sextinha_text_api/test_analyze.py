from fastapi.testclient import TestClient
from services.sextinha_text_api.app.main import app

client = TestClient(app)

def test_analyze_ok():
    resp = client.post("/analyze", json={"text": "Sextinha é braba demais!"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["length"] >= 1
    # "Sextinha é braba demais" -> 4 palavras
    assert data["word_count"] == 4
    assert data["preview"].startswith("Sextinha é braba")

def test_analyze_trim_and_preview():
    long_text = "  A " + ("x" * 200)
    resp = client.post("/analyze", json={"text": long_text})
    assert resp.status_code == 200
    data = resp.json()
    assert data["length"] == len(long_text.strip())
    assert data["preview"].endswith("…")  # cortado com reticência

def test_analyze_empty_rejected():
    resp = client.post("/analyze", json={"text": "   "})
    assert resp.status_code in (400, 422)
