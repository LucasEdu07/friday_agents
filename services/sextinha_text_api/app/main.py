from fastapi import FastAPI
from fastapi.responses import JSONResponse

from services.shared.health import HealthChecker, ProbeStatus

from .models import AnalyzeRequest, AnalyzeResponse

app = FastAPI(title="Sextinha Text API", version="0.1.0")


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
