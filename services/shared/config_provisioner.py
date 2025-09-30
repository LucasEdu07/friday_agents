# services/shared/config_provisioner.py
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import yaml

from . import tenant_repo
from .config_schema import (
    TenantConfig,
    TenantCORS,
    TenantFeatures,
    TenantLimits,
    TenantModels,
)

TENANTS_DIR = Path(__file__).parent / "tenants"


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _default_features() -> TenantFeatures:
    return TenantFeatures(
        enable_text=True,
        enable_vision=True,
        enable_ocr=False,
    )


def _default_limits() -> TenantLimits:
    return TenantLimits(
        max_input_tokens=4096,
        max_output_tokens=1024,
        max_images_per_request=4,
    )


def _default_models() -> TenantModels:
    return TenantModels(
        text_model="gpt-4o-mini",
        vision_model="gpt-4o",
        ocr_model="tesseract",
    )


def _default_cors() -> TenantCORS:
    return TenantCORS(origins=[])


def _tenant_dir(tenant_id: str) -> Path:
    return TENANTS_DIR / tenant_id


def _tenant_config_path(tenant_id: str) -> Path:
    return _tenant_dir(tenant_id) / "config.yaml"


def _compose_config(tenant_id: str, name: str) -> TenantConfig:
    features = _default_features()
    limits = _default_limits()
    models = _default_models()
    cors = _default_cors()

    # Use cast para satisfazer o TypedDict
    cfg = cast(
        TenantConfig,
        {
            "id": tenant_id,
            "name": name,
            "features": features,
            "limits": limits,
            "models": models,
            "cors": cors,
        },
    )
    return cfg


def _write_yaml(path: Path, data: Mapping[str, Any]) -> None:
    _ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(dict(data), f, sort_keys=False, allow_unicode=True)


def provision_single(tenant_id: str, name: str, *, overwrite: bool = False) -> bool:
    """
    Cria/atualiza tenants/<id>/config.yaml.
    Retorna True se escreveu arquivo, False se manteve o existente.
    """
    cfg = _compose_config(tenant_id, name)
    dst = _tenant_config_path(tenant_id)

    if dst.exists() and not overwrite:
        return False

    _write_yaml(dst, cast(Mapping[str, Any], cfg))
    return True


def sync_from_db(*, overwrite: bool = False) -> int:
    """
    Percorre a tabela de tenants e garante um config.yaml para cada.
    Retorna o número de arquivos escritos nesta execução.
    """
    rows = tenant_repo.list_all_tenants()
    written = 0
    for row in rows:
        tenant_id: str | None = None
        name: str | None = None

        if isinstance(row, dict):
            tenant_id = str(row.get("tenant_id") or row.get("id") or "")
            name = str(row.get("name") or "")
        else:
            tid = getattr(row, "tenant_id", None) or getattr(row, "id", None)
            nm = getattr(row, "name", None)
            if tid is not None:
                tenant_id = str(tid)
            if nm is not None:
                name = str(nm)

        if not tenant_id or not name:
            continue

        if provision_single(tenant_id, name, overwrite=overwrite):
            written += 1

    return written
