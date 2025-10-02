# services/sextinha_text_api/app/main.py
import os
from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from services.shared.config_loader import reload_all_configs
from services.shared.config_provisioner import sync_from_db
from services.shared.health import HealthChecker, ProbeStatus
from services.shared.middleware.cors import CORSMiddlewarePerTenant
from services.shared.middleware.rate_limit import RateLimitMiddlewarePerTenant
from services.shared.middleware_utils import RequestIdMiddleware, TenantMiddleware

from ...shared.app_middleware import apply_middlewares
from .admin.dev_router import router as admin_dev_router
from .api.v1.router import router as v1_router
from .models import AnalyzeRequest, AnalyzeResponse


class SextinhaFastAPI(FastAPI):
    def openapi(self) -> dict[str, Any]:
        if self.openapi_schema:
            return self.openapi_schema

        schema = get_openapi(
            title=self.title,
            version=self.version,
            description=self.description,
            routes=self.routes,
        )

        schema.setdefault("info", {}).update(
            {
                "contact": {"name": "Friday Agents", "url": "https://example.com"},
                "license": {"name": "MIT"},
            }
        )
        schema["tags"] = [{"name": "v1"}, {"name": "ops"}, {"name": "admin"}]

        comps = schema.setdefault("components", {})
        comps.setdefault("securitySchemes", {})["ApiKeyAuth"] = {
            "type": "apiKey",
            "in": "header",
            "name": "x-api-key",
        }

        for path, path_item in schema.get("paths", {}).items():
            is_v1 = path.startswith("/v1/")
            for method_obj in path_item.values():
                if not isinstance(method_obj, dict):
                    continue
                if is_v1:
                    method_obj.setdefault("security", [{"ApiKeyAuth": []}])
                else:
                    method_obj.pop("security", None)

        self.openapi_schema = schema
        return schema


app = SextinhaFastAPI(
    title="Sextinha Text API",
    version="1.0",
    description="API do Sextinha Text (multi-tenant por x-api-key).",
    swagger_ui_parameters={"persistAuthorization": True, "displayRequestDuration": True},
)

# ORDEM IMPORTA (o último adicionado roda primeiro / outermost):
# Queremos: RequestId (outermost) -> Tenant -> RateLimit -> CORS (innermost)
app.add_middleware(CORSMiddlewarePerTenant)  # innermost
app.add_middleware(RateLimitMiddlewarePerTenant)  # entre Tenant e CORS
app.add_middleware(TenantMiddleware)  # middle
app.add_middleware(RequestIdMiddleware)  # outermost

# Rotas v1
apply_middlewares(app)
app.include_router(v1_router, tags=["v1"])


# --- rotas auxiliares/ops ---
def _count_words(txt: str) -> int:
    import re

    tokens = re.findall(r"\b\w+\b", txt, flags=re.UNICODE)
    return len(tokens)


@app.post("/analyze", response_model=AnalyzeResponse, tags=["ops"])
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    txt = req.text
    length = len(txt)
    word_count = _count_words(txt)
    preview = txt[:120] + ("…" if len(txt) > 120 else "")
    return AnalyzeResponse(length=length, word_count=word_count, preview=preview)


checker = HealthChecker(service_name="sextinha_text_api")


@app.on_event("startup")
async def _startup_health() -> None:
    checker.register("app_started", lambda: True)


@app.get("/health", response_model=ProbeStatus, tags=["ops"])
async def health_probe() -> ProbeStatus:
    return await checker.health()


@app.get(
    "/readiness", response_model=ProbeStatus, responses={503: {"model": ProbeStatus}}, tags=["ops"]
)
async def readiness_probe():
    ok, payload = await checker.readiness()
    if ok:
        return payload
    return JSONResponse(status_code=503, content=payload.model_dump())


admin = APIRouter(tags=["admin"])


def _dev_only() -> bool:
    return os.getenv("ENV", "dev") == "dev"


@admin.post("/admin/reload-config")
def reload_configs():
    if not _dev_only():
        return JSONResponse({"detail": "disabled"}, status_code=403)
    reload_all_configs()
    return {"reloaded": True}


@admin.post("/admin/sync-configs")
def sync_configs():
    if not _dev_only():
        return JSONResponse({"detail": "disabled"}, status_code=403)
    n = sync_from_db(overwrite=False)
    return {"synced": n}


app.include_router(admin)

app.include_router(admin_dev_router)
