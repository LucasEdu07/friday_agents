from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from services.shared.health import HealthChecker, ProbeStatus
from services.shared.middleware import TenantMiddleware

from .api.v1.router import router as v1_router
from .models import AnalyzeRequest, AnalyzeResponse


class SextinhaFastAPI(FastAPI):
    def openapi(self) -> dict[str, Any]:  # mypy-friendly
        if self.openapi_schema:
            return self.openapi_schema
        schema = get_openapi(title=self.title, version=self.version, routes=self.routes)
        schema.setdefault("components", {}).setdefault("securitySchemes", {})["ApiKeyAuth"] = {
            "type": "apiKey",
            "in": "header",
            "name": "x-api-key",
        }
        for path in schema["paths"].values():
            for method in path.values():
                method.setdefault("security", [{"ApiKeyAuth": []}])
        self.openapi_schema = schema
        return schema


# ✅ cria UMA única app, adiciona middleware e registra router v1
app = SextinhaFastAPI(title="Sextinha Text API", version="1.0")
app.add_middleware(TenantMiddleware)
app.include_router(v1_router, prefix="/v1")


def _count_words(txt: str) -> int:
    import re

    tokens = re.findall(r"\b\w+\b", txt, flags=re.UNICODE)
    return len(tokens)


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    txt = req.text  # já vem stripado e validado pelo Pydantic
    length = len(txt)
    word_count = _count_words(txt)
    preview = txt[:120] + ("…" if len(txt) > 120 else "")
    return AnalyzeResponse(length=length, word_count=word_count, preview=preview)


# --- health/readiness padronizados ---
checker = HealthChecker(service_name="sextinha_text_api")


@app.on_event("startup")
async def _startup_health() -> None:
    # Registre checks reais quando houver (DB, fila, modelos, etc.)
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
