# services/sextinha_text_api/app/api/v1/router.py
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, Request

router = APIRouter(prefix="/v1", tags=["v1"])


def _as_dict(model_or_dict: Any) -> Mapping[str, Any] | None:
    if model_or_dict is None:
        return None
    if isinstance(model_or_dict, dict):
        return model_or_dict
    if hasattr(model_or_dict, "model_dump"):
        try:
            return model_or_dict.model_dump()
        except Exception:
            pass
    if hasattr(model_or_dict, "dict"):
        try:
            return model_or_dict.dict()  # pydantic v1
        except Exception:
            pass
    return None


@router.get("/ping", summary="Ping")
def ping(request: Request):
    tenant = getattr(request.state, "tenant", None)
    who = tenant.name if tenant else "unknown"
    return {"message": f"Pong from {who}"}


@router.get("/debug/whoami", summary="Whoami")
def whoami(request: Request):
    t = getattr(request.state, "tenant", None)
    cfg = getattr(request.state, "tenant_config", None)
    d = _as_dict(cfg)

    return {
        "tenant_id": t.id if t else None,
        "tenant_name": t.name if t else None,
        "features": d.get("features") if isinstance(d, dict) else None,
        "limits": d.get("limits") if isinstance(d, dict) else None,
        "models": d.get("models") if isinstance(d, dict) else None,
    }
