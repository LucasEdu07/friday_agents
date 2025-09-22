from fastapi import HTTPException
from starlette.requests import Request as StarletteRequest

from . import tenant_repo
from .tenant_context import TenantInfo, get_current_tenant


def require_tenant(request: StarletteRequest) -> TenantInfo:
    """
    Dependência para endpoints protegidos: garante que há um Tenant resolvido.
    - Primeiro tenta o contexto (setado pelo middleware).
    - Se não houver, faz fallback pegando x-api-key do header e consultando o repo.
    """
    tenant = get_current_tenant()
    if tenant:
        return tenant

    api_key = request.headers.get("x-api-key")
    if not api_key:
        raise HTTPException(status_code=401, detail="x-api-key is required")

    try:
        resolved = tenant_repo.find_tenant_by_api_key(api_key)
    except tenant_repo.TenantRepoUnavailable as err:
        raise HTTPException(status_code=503, detail="Tenant repository unavailable") from err

    if resolved is None:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return resolved
