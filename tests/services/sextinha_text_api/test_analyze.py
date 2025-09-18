from fastapi.testclient import TestClient

from services.sextinha_text_api.app.main import app

client = TestClient(app)

def test_analyze_ok_simple():
    r = client.post("/analyze", json={"text": "Sextinha é braba demais!"})
    assert r.status_code == 200
    data = r.json()
    assert data["word_count"] >= 4
    assert data["length"] == len("Sextinha é braba demais!")

def test_analyze_trim_and_preview_ellipsis():
    txt = "  A " + ("x" * 200)
    r = client.post("/analyze", json={"text": txt})
    assert r.status_code == 200
    data = r.json()
    assert data["length"] == len(txt.strip())
    assert data["preview"].endswith("…")
    assert len(data["preview"]) <= 121  # 120 + reticência

def test_analyze_unicode_tokens():
    r = client.post("/analyze", json={"text": "Olá, mundo! 你好，世界"})
    assert r.status_code == 200
    data = r.json()
    assert data["word_count"] >= 2  # depende do tokenizador simples

def test_analyze_empty_whitespace_422():
    r = client.post("/analyze", json={"text": "   "})
    assert r.status_code == 422  # validado via Pydantic (depois da #1003)

def test_analyze_extra_field_forbidden():
    r = client.post("/analyze", json={"text": "ok", "extra": "nope"})
    assert r.status_code == 422  # extra="forbid" no AppBaseModel
