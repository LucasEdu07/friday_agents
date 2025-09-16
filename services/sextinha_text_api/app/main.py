from fastapi import FastAPI, HTTPException
try:
    from .models import AnalyzeRequest, AnalyzeResponse
except ImportError:
    from services.sextinha_text_api.app.models import AnalyzeRequest, AnalyzeResponse

app = FastAPI(title="Sextinha Text API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "sextinha_text_api"}

def _count_words(txt: str) -> int:
    import re
    tokens = re.findall(r"\b\w+\b", txt, flags=re.UNICODE)
    return len(tokens)

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    txt = req.text.strip()
    if not txt:
        raise HTTPException(status_code=422, detail="Texto vazio")
    length = len(txt)
    word_count = _count_words(txt)
    preview = txt[:120] + ("…" if len(txt) > 120 else "")
    return AnalyzeResponse(length=length, word_count=word_count, preview=preview)
