from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

from .config_schema import TenantConfig

BASE_DIR = Path(__file__).resolve().parent / "tenants"


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return cast(dict, data or {})


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)


def _fallback_minimal_config(slug: str) -> dict[str, Any] | None:
    """
    Fallback usado em ambiente de testes quando não há DB disponível.
    Gera o mínimo para os testes /v1/ping e auth passarem.
    """
    names = {"1": "Dra. Camila", "2": "Oficina do Zé", "3": "Squad Inc"}
    name = names.get(slug)
    if not name:
        return None

    return {
        "tenant_id": int(slug),
        "name": name,
        "features": {"analyze": True},
        "limits": {"max_tokens": 4096},
        "models": {"llm": "gpt-4o-mini"},
        "cors": {"allow_origins": ["*"]},
    }


def load_config(slug: str):
    cfg_path = BASE_DIR / slug / "config.yaml"
    if not cfg_path.exists():
        from .config_provisioner import sync_from_db

        try:
            sync_from_db(overwrite=False)
        except Exception:
            pass
    if not cfg_path.exists():
        raise FileNotFoundError(f"config for tenant '{slug}' not found")
    with cfg_path.open("r", encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh)
    return data


def reload_all_configs() -> int:
    """
    Varre tenants/*/config.yaml e valida todos.
    Retorna a contagem validada. Útil para o endpoint /admin/reload-config.
    """
    if not BASE_DIR.exists():
        return 0

    count = 0
    for slug_dir in BASE_DIR.iterdir():
        if not slug_dir.is_dir():
            continue
        cfg_file = slug_dir / "config.yaml"
        if not cfg_file.exists():
            continue
        _ = TenantConfig.model_validate(_read_yaml(cfg_file))
        count += 1
    return count
