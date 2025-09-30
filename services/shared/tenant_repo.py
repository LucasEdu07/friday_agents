# services/shared/tenant_repo.py
from __future__ import annotations

import os
from typing import TypedDict

import psycopg


class TenantRow(TypedDict):
    tenant_id: int
    name: str


class TenantRepoUnavailable(Exception):
    pass


DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

# Fallback hardcoded usado em dev/test quando não há DB
_FALLBACK_TENANTS: list[TenantRow] = [
    {"tenant_id": 1, "name": "Dra. Camila"},
    {"tenant_id": 2, "name": "Oficina do Zé"},
    {"tenant_id": 3, "name": "Squad Inc"},
]
_FALLBACK_API_KEYS = {
    "camila123": _FALLBACK_TENANTS[0],
    "zeoficina456": _FALLBACK_TENANTS[1],
    "squad789": _FALLBACK_TENANTS[2],
}


def list_all_tenants() -> list[TenantRow]:
    """
    Se DATABASE_URL não estiver definido, devolve o fallback local (3 tenants).
    Com DB, lê da tabela tenants (id, name).
    """
    if not DATABASE_URL:
        return list(_FALLBACK_TENANTS)

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("select id as tenant_id, name from tenants order by id;")
                rows = cur.fetchall()
                return [{"tenant_id": r[0], "name": r[1]} for r in rows]
    except Exception as e:
        raise TenantRepoUnavailable() from e


def find_tenant_by_api_key(api_key: str) -> TenantRow | None:
    """
    Se DATABASE_URL não estiver definido, usa o fallback local de api_keys.
    Com DB, consulta join api_keys -> tenants.
    """
    if not DATABASE_URL:
        return _FALLBACK_API_KEYS.get(api_key)

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select t.id, t.name
                      from api_keys k
                      join tenants t on t.id = k.tenant_id
                     where k.key = %s
                     limit 1;
                    """,
                    (api_key,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {"tenant_id": row[0], "name": row[1]}
    except Exception as e:
        raise TenantRepoUnavailable() from e
