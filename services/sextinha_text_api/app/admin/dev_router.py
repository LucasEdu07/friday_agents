# services/sextinha_text_api/app/admin/dev_router.py
from __future__ import annotations

import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from services.shared.tenant_repo import list_all_tenants

router = APIRouter(tags=["admin"])

# --- helpers / guards ---------------------------------------------------------


def _dev_only() -> None:
    """
    Bloqueia o router inteiro fora de ENV=dev.
    Usar como dependency em cada rota.
    """
    if os.getenv("ENV", "dev") != "dev":
        # 403 para não “denunciar” a existência em prod.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="disabled",
        )


DevOnly = Annotated[None, Depends(_dev_only)]

# --- models (mínimos por enquanto) -------------------------------------------


class TenantCreateIn(BaseModel):
    tenant_id: str
    name: str


class ApiKeyRotateIn(BaseModel):
    tenant_id: str
    reason: str | None = None


class ApiKeyRevokeIn(BaseModel):
    tenant_id: str
    key_name: str
    reason: str | None = None


# --- rotas (list ok; demais stubs p/ #3017) ----------------------------------


@router.get("/admin/dev/tenants")
def dev_list_tenants(_guard: DevOnly) -> list[dict]:
    """
    Lista tenants conhecidos (1 linha por tenant_id).
    Usa a tabela tenants_api_keys (apenas ativos).
    """
    rows = list_all_tenants()
    # já vem como list[TypedDict]; converter para dict “simples” p/ OpenAPI bonito
    return [dict(r) for r in rows]


@router.post("/admin/dev/tenants")
def dev_create_tenant(_guard: DevOnly, payload: TenantCreateIn) -> dict:
    # stub: implementar na #3017
    return {
        "detail": "not-implemented-yet",
        "echo": payload.model_dump(),
    }


@router.post("/admin/dev/keys/rotate")
def dev_rotate_key(_guard: DevOnly, payload: ApiKeyRotateIn) -> dict:
    # stub: implementar na #3017
    return {
        "detail": "not-implemented-yet",
        "echo": payload.model_dump(),
    }


@router.post("/admin/dev/keys/revoke")
def dev_revoke_key(_guard: DevOnly, payload: ApiKeyRevokeIn) -> dict:
    # stub: implementar na #3017
    return {
        "detail": "not-implemented-yet",
        "echo": payload.model_dump(),
    }
