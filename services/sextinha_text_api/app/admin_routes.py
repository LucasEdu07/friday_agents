from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from services.shared import tenant_repo
from services.shared.admin_guard import ensure_admin_enabled
from services.shared.key_service import create_key, list_keys, revoke_key, rotate_key

router = APIRouter(prefix="/admin", tags=["admin"])


# —————————— Models ——————————


class CreateKeyIn(BaseModel):
    name: str | None = Field(default=None, description="Nome amigável; opcional")


class CreateKeyOut(BaseModel):
    tenant_id: str
    name: str
    api_key_plain: str  # retornada apenas uma vez


class RotateKeyIn(BaseModel):
    previous_name: str | None = None
    new_name: str | None = None


class RotateKeyOut(BaseModel):
    tenant_id: str
    name: str
    api_key_plain: str  # retornada apenas uma vez


class RevokeKeyIn(BaseModel):
    name: str


class KeyRowOut(BaseModel):
    name: str
    revoked: bool


# —————————— Endpoints ——————————


@router.get("/tenants", dependencies=[Depends(ensure_admin_enabled)])
def list_tenants():
    # usa o helper já existente
    return tenant_repo.list_all_tenants()


@router.get(
    "/tenants/{tenant_id}/keys",
    response_model=list[KeyRowOut],
    dependencies=[Depends(ensure_admin_enabled)],
)
def list_tenant_keys(tenant_id: str):
    rows = list_keys(tenant_id)
    return [KeyRowOut.model_validate(r, from_attributes=True) for r in rows]


@router.post(
    "/tenants/{tenant_id}/keys",
    response_model=CreateKeyOut,
    dependencies=[Depends(ensure_admin_enabled)],
)
def create_tenant_key(tenant_id: str, body: CreateKeyIn):
    name, api_key_plain = create_key(tenant_id, name=body.name)
    return CreateKeyOut(tenant_id=tenant_id, name=name, api_key_plain=api_key_plain)


@router.post(
    "/tenants/{tenant_id}/keys:rotate",
    response_model=RotateKeyOut,
    dependencies=[Depends(ensure_admin_enabled)],
)
def rotate_tenant_key(tenant_id: str, body: RotateKeyIn):
    name, api_key_plain = rotate_key(
        tenant_id,
        previous_name=body.previous_name,
        new_name=body.new_name,
    )
    return RotateKeyOut(tenant_id=tenant_id, name=name, api_key_plain=api_key_plain)


@router.post(
    "/tenants/{tenant_id}/keys:revoke",
    status_code=204,
    dependencies=[Depends(ensure_admin_enabled)],
)
def revoke_tenant_key(tenant_id: str, body: RevokeKeyIn):
    n = revoke_key(tenant_id, body.name)
    if n == 0:
        raise HTTPException(status_code=404, detail="Key not found or already revoked")
