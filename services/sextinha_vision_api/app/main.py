import base64

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from services.shared.health import HealthChecker, ProbeStatus
from services.shared.middleware import RequestIdMiddleware, TenantMiddleware

from .models import VisionAnalyzeRequest, VisionAnalyzeResponse

app = FastAPI(title="Sextinha Vision API", version="0.1.0")

# ✅ ORDEM IMPORTA: RequestId antes de Tenant
app.add_middleware(RequestIdMiddleware)
app.add_middleware(TenantMiddleware)


def _detect_image_format(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8"):
        return "jpeg"
    return "unknown"


# --------- ROTAS ---------


# ✅ Versão versionada (protegida pelo TenantMiddleware via /v1/*)
@app.post("/v1/vision/analyze", response_model=VisionAnalyzeResponse, tags=["v1"])
def vision_analyze_v1(req: VisionAnalyzeRequest) -> VisionAnalyzeResponse:
    data = base64.b64decode(req.image_base64, validate=True)
    fmt = _detect_image_format(data)
    return VisionAnalyzeResponse(size_bytes=len(data), format=fmt)


# (Opcional) Alias não versionado para compatibilidade. Fica público.
# Remova se não quiser manter esse caminho legacy.
@app.post("/vision/analyze", response_model=VisionAnalyzeResponse, tags=["ops"])
def vision_analyze_legacy(req: VisionAnalyzeRequest) -> VisionAnalyzeResponse:
    data = base64.b64decode(req.image_base64, validate=True)
    fmt = _detect_image_format(data)
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
