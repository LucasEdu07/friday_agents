from typing import Any
from urllib.request import Request

from fastapi import FastAPI, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from services.shared.health import HealthChecker, ProbeStatus
from services.shared.middleware import TenantMiddleware
from services.shared.tenant_context import get_current_tenant

from .models import AnalyzeRequest, AnalyzeResponse

app = FastAPI(title="Sextinha Text API", version="0.1.0")
app.add_middleware(TenantMiddleware)


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


app = SextinhaFastAPI(title="Sextinha Text API", version="1.0")


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


@app.get("/v1/ping")
def ping(request: Request):
    tenant = get_current_tenant()
    if not tenant:
        # Fallback: se o middleware não injetou o tenant (ex.: coleta de testes),
        # o endpoint mesmo valida o header e resolve o tenant.
        api_key = request.headers.get("x-api-key")
        if not api_key:
            raise HTTPException(status_code=401, detail="x-api-key is required")

        # Import tardio para respeitar o monkeypatch nos testes e o lazy import do psycopg
        from services.shared import tenant_repo

        try:
            resolved = tenant_repo.find_tenant_by_api_key(api_key)
        except tenant_repo.TenantRepoUnavailable as err:
            raise HTTPException(status_code=503, detail="Tenant repository unavailable") from err

        if resolved is None:
            raise HTTPException(status_code=403, detail="Invalid API key")
        tenant = resolved

    return {"message": f"Pong from {tenant.name}"}
