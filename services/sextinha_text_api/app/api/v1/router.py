from typing import Annotated

from fastapi import APIRouter, Depends

from services.shared.auth import require_tenant
from services.shared.tenant_context import TenantInfo

router = APIRouter(tags=["v1"])

TenantDep = Annotated[TenantInfo, Depends(require_tenant)]


@router.get("/ping")
def ping(tenant: TenantDep):
    return {"message": f"Pong from {tenant.name}"}
