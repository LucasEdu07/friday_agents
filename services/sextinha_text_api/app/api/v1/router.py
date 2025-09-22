from fastapi import APIRouter, HTTPException
from starlette.requests import Request as StarletteRequest

from services.shared.tenant_context import get_current_tenant

router = APIRouter(tags=["v1"])


@router.get("/ping")
def ping(request: StarletteRequest):
    """
    Mantém o comportamento atual:
    - Depende do middleware para validar x-api-key
    - Se o middleware não setar o tenant (ex.: coleta de testes), faz fallback local
    """
    tenant = get_current_tenant()
    if not tenant:
        api_key = request.headers.get("x-api-key")
        if not api_key:
            raise HTTPException(status_code=401, detail="x-api-key is required")

        # Import tardio para respeitar monkeypatch e lazy import do psycopg no CI
        from services.shared import tenant_repo

        try:
            resolved = tenant_repo.find_tenant_by_api_key(api_key)
        except tenant_repo.TenantRepoUnavailable as err:
            raise HTTPException(status_code=503, detail="Tenant repository unavailable") from err

        if resolved is None:
            raise HTTPException(status_code=403, detail="Invalid API key")
        tenant = resolved

    return {"message": f"Pong from {tenant.name}"}
