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

        schema = get_openapi(
            title=self.title,
            version=self.version,
            description=self.description,
            routes=self.routes,
        )

        # Metadados bonitinhos
        schema.setdefault("info", {}).update(
            {
                "contact": {"name": "Friday Agents", "url": "https://example.com"},
                "license": {"name": "MIT"},
            }
        )
        # Tag order opcional (v1 primeiro, ops depois)
        schema["tags"] = [{"name": "v1"}, {"name": "ops"}]

        # Security scheme: ApiKeyAuth via header x-api-key
        comps = schema.setdefault("components", {})
        comps.setdefault("securitySchemes", {})["ApiKeyAuth"] = {
            "type": "apiKey",
            "in": "header",
            "name": "x-api-key",
        }

        # Exigir API key apenas nas rotas /v1/*
        for path, path_item in schema.get("paths", {}).items():
            is_v1 = path.startswith("/v1/")
            for method_obj in path_item.values():
                if not isinstance(method_obj, dict):
                    continue
                if is_v1:
                    method_obj.setdefault("security", [{"ApiKeyAuth": []}])
                else:
                    # Garante públicas (readiness, docs, analyze)
                    if "security" in method_obj:
                        method_obj.pop("security", None)

        self.openapi_schema = schema
        return schema

    # ✅ cria uma única app com swagger que persiste autorização


app = SextinhaFastAPI(
    title="Sextinha Text API",
    version="1.0",
    description="API de exemplo do Sextinha Text (multi-tenant por x-api-key).",
    swagger_ui_parameters={"persistAuthorization": True, "displayRequestDuration": True},
)
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
