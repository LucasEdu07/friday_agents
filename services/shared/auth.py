# services/shared/auth.py
from __future__ import annotations

from fastapi import HTTPException, Request, Security
from fastapi.security.api_key import APIKeyHeader

from . import tenant_repo
from .tenant_context import TenantInfo

# Define o esquema de segurança para o OpenAPI e para as rotas /v1
_api_key_header = APIKeyHeader(name="x-api-key", auto_error=True)


def _to_tenant_info(tenant_obj: object) -> TenantInfo:
    def pick(*names: str) -> str | None:
        for n in names:
            if hasattr(tenant_obj, n):
                v = getattr(tenant_obj, n)
                if v:
                    return str(v)
        return None

    tid = pick("tenant_id", "id")
    name = pick("name")
    slug = pick("slug")
    api_key = pick("api_key", "key") or ""
    status = pick("status") or "active"

    if not tid:
        tid = slug or name or "unknown"

    display_name = name or slug or tid

    return TenantInfo(
        id=str(tid),
        name=str(display_name),
        api_key=str(api_key),
        status=str(status),
    )


def require_api_key(request: Request) -> TenantInfo:
    """
    Lê x-api-key diretamente do Request.headers, resolve e retorna TenantInfo.
    Útil quando você não precisa do 'security' no OpenAPI.
    """
    api_key = request.headers.get("x-api-key")
    if not api_key:
        raise HTTPException(status_code=401, detail="x-api-key is required")

    try:
        tenant_row = tenant_repo.find_tenant_by_api_key(api_key)
    except tenant_repo.TenantRepoUnavailable as err:
        raise HTTPException(status_code=503, detail="Tenant repository unavailable") from err

    if tenant_row is None:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return _to_tenant_info(tenant_row)


async def require_tenant(api_key: str = Security(_api_key_header)) -> TenantInfo:
    """
    Dependência para ser usada no router (dependencies=[...]) ou nos endpoints.
    Usa Security(APIKeyHeader) para:
      - validar a x-api-key
      - e fazer o OpenAPI incluir 'security' nas rotas /v1
    Retorna TenantInfo.
    """
    try:
        tenant_row = tenant_repo.find_tenant_by_api_key(api_key)
    except tenant_repo.TenantRepoUnavailable as err:
        raise HTTPException(status_code=503, detail="Tenant repository unavailable") from err

    if tenant_row is None:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return _to_tenant_info(tenant_row)
