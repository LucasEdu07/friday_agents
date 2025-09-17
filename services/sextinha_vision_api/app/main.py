from fastapi import FastAPI, HTTPException
import base64
import binascii

try:
    from .models import VisionAnalyzeRequest, VisionAnalyzeResponse
except ImportError:
    from services.sextinha_vision_api.app.models import VisionAnalyzeRequest, VisionAnalyzeResponse

app = FastAPI(title="Sextinha Vision API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "sextinha_vision_api"}

@app.post("/vision/analyze", response_model=VisionAnalyzeResponse)
def vision_analyze(req: VisionAnalyzeRequest):
    try:
        data = base64.b64decode(req.image_base64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="image_base64 inválido")

    fmt = "unknown"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        fmt = "png"
    elif data.startswith(b"\xff\xd8"):
        fmt = "jpeg"

    return VisionAnalyzeResponse(size_bytes=len(data), format=fmt)
