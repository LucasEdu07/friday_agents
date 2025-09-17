import base64

from fastapi import FastAPI

from .models import VisionAnalyzeRequest, VisionAnalyzeResponse

app = FastAPI(title="Sextinha Vision API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "sextinha_vision_api"}

@app.post("/vision/analyze", response_model=VisionAnalyzeResponse)
def vision_analyze(req: VisionAnalyzeRequest):
    data = base64.b64decode(req.image_base64, validate=True)

    fmt = "unknown"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        fmt = "png"
    elif data.startswith(b"\xff\xd8"):
        fmt = "jpeg"

    return VisionAnalyzeResponse(size_bytes=len(data), format=fmt)
