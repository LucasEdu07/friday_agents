import base64

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from services.shared.health import HealthChecker, ProbeStatus

from .models import VisionAnalyzeRequest, VisionAnalyzeResponse

app = FastAPI(title="Sextinha Vision API", version="0.1.0")


@app.post("/vision/analyze", response_model=VisionAnalyzeResponse)
def vision_analyze(req: VisionAnalyzeRequest) -> VisionAnalyzeResponse:
    data = base64.b64decode(req.image_base64, validate=True)

    fmt = "unknown"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        fmt = "png"
    elif data.startswith(b"\xff\xd8"):
        fmt = "jpeg"

    return VisionAnalyzeResponse(size_bytes=len(data), format=fmt)


# --- health/readiness padronizados ---
checker = HealthChecker(service_name="sextinha_vision_api")


@app.on_event("startup")
async def _startup_health() -> None:
    checker.register("app_started", lambda: True)


@app.get("/health", response_model=ProbeStatus, tags=["ops"])
async def health_probe() -> ProbeStatus:
    return await checker.health()


@app.get(
    "/readiness",
    response_model=ProbeStatus,
    responses={503: {"model": ProbeStatus}},
    tags=["ops"],
)
async def readiness_probe():
    ok, payload = await checker.readiness()
    if ok:
        return payload
    return JSONResponse(status_code=503, content=payload.model_dump())
