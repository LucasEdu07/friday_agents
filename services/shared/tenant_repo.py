# services/shared/tenant_repo.py
import importlib
import logging
import os
from typing import Any

from .tenant_context import TenantInfo

logger = logging.getLogger("tenant_repo")

DSN = (
    os.getenv("DATABASE_URL")
    or os.getenv("DB_URL")
    or "postgresql://postgres:postgres@localhost:5432/friday_agents"
)


class TenantRepoUnavailable(Exception):
    pass


def _load_psycopg() -> Any:
    try:
        return importlib.import_module("psycopg")
    except Exception as e:
        # No CI, sem driver: o middleware converte p/ 503 (e nos testes a função é stubada)
        raise TenantRepoUnavailable("psycopg not installed") from e


def find_tenant_by_api_key(api_key: str) -> TenantInfo | None:
    psycopg = _load_psycopg()  # lazy import (evita ModuleNotFoundError na importação do módulo)
    try:
        with psycopg.connect(DSN) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, api_key, status FROM tenants "
                    "WHERE api_key = %s AND status = 'active' LIMIT 1",
                    (api_key,),
                )
                row = cur.fetchone()
                if row:
                    return TenantInfo(id=row[0], name=row[1], api_key=row[2], status=row[3])
                return None
    except Exception as e:
        logger.exception("DB error while fetching tenant by api_key")
        raise TenantRepoUnavailable from e
