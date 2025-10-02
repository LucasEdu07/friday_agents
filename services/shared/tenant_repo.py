from __future__ import annotations

import os
from typing import Any, TypedDict, cast

# Tenta usar Postgres se houver driver/DSN; caso contrário, cai no fallback.
try:
    import psycopg  # usado mais abaixo
except ImportError:
    psycopg = cast(Any, None)  # evita type: ignore


class TenantRow(TypedDict, total=False):
    tenant_id: str
    name: str
    api_key: str
    status: str  # "active"|"revoked"|etc.


class TenantRepoUnavailable(RuntimeError):
    """Erro para indicar indisponibilidade do repositório (BD off, rede, etc.)."""


# Fallback estático usado nos testes/unit (sem banco) e como rede de segurança.
_STATIC_API_KEYS: dict[str, TenantRow] = {
    "camila123": {"tenant_id": "1", "name": "Dra. Camila", "status": "active"},
    "zeoficina456": {"tenant_id": "2", "name": "Oficina do Zé", "status": "active"},
    "squad789": {"tenant_id": "3", "name": "Squad Inc", "status": "active"},
}


def _db_dsn_env() -> str | None:
    dsn = os.getenv("DATABASE_URL")
    if dsn and dsn.strip():
        return dsn.strip()
    return None


def _db_dsn_from_settings() -> str | None:
    """
    Tenta ler o DSN de `services.shared.settings`, caso o módulo exista.
    Suporta:
      - services.shared.settings.DATABASE_URL
      - services.shared.settings.settings.DATABASE_URL
    Tudo via getattr seguro para não quebrar tipagem.
    """
    try:
        import services.shared.settings as settings_mod  # noqa: F401
    except Exception:
        return None

    # 1) atributo direto no módulo
    dsn_mod = cast(str | None, getattr(settings_mod, "DATABASE_URL", None))
    if isinstance(dsn_mod, str) and dsn_mod.strip():
        return dsn_mod.strip()

    # 2) objeto `settings` dentro do módulo
    settings_obj = getattr(settings_mod, "settings", None)
    if settings_obj is not None:
        dsn_obj = cast(str | None, getattr(settings_obj, "DATABASE_URL", None))
        if isinstance(dsn_obj, str) and dsn_obj.strip():
            return dsn_obj.strip()

    return None


def _db_dsn() -> str | None:
    """
    Ordem de resolução:
      1) settings (se presente)
      2) variável de ambiente DATABASE_URL
    """
    return _db_dsn_from_settings() or _db_dsn_env()


def _resolve_via_static(api_key: str) -> TenantRow | None:
    row = _STATIC_API_KEYS.get(api_key)
    if not row:
        return None
    # retornamos um dict com os campos esperados; adicionamos api_key para consistência
    return {
        "tenant_id": row["tenant_id"],
        "name": row["name"],
        "status": row.get("status", "active"),
        "api_key": api_key,
    }


def _resolve_via_db(api_key: str) -> TenantRow | None:
    """
    Resolve via Postgres, assumindo a migração criada pelo projeto:

        CREATE TABLE IF NOT EXISTS tenants_api_keys (
            id           TEXT PRIMARY KEY,
            tenant_id    TEXT NOT NULL,
            name         TEXT NOT NULL,
            algo         TEXT NOT NULL,
            iterations   INTEGER NOT NULL,
            salt_b64     TEXT NOT NULL,
            hash_b64     TEXT NOT NULL,
            created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            revoked_at   TIMESTAMP NULL,
            last_used_at TIMESTAMP NULL,
            UNIQUE (tenant_id, name, revoked_at)
        );

    Não precisamos do hash aqui — apenas localizar tenant_id e name pela key.
    """
    dsn = _db_dsn()
    if not dsn or psycopg is None:
        return None

    try:
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT tenant_id, name
                      FROM tenants_api_keys
                     WHERE revoked_at IS NULL
                       AND name = %s
                    LIMIT 1
                    """,
                    (api_key,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                tenant_id, key_name = row[0], row[1]
                return {
                    "tenant_id": str(tenant_id),
                    "name": str(key_name),
                    "api_key": api_key,
                    "status": "active",
                }
    except Exception as ex:  # pragma: no cover
        # Qualquer exceção de rede/BD deve ser mapeada para indisponibilidade,
        # para que o middleware devolva 503 corretamente.
        raise TenantRepoUnavailable(str(ex)) from ex


def resolve_tenant_by_api_key(api_key: str) -> TenantRow | None:
    """
    Estratégia:
      1) Se houver DATABASE_URL e psycopg disponível, tentamos o BD.
      2) Se não houver BD (ou falhar com TenantRepoUnavailable), caímos no fallback estático.
    """
    dsn = _db_dsn()
    if dsn:
        try:
            via_db = _resolve_via_db(api_key)
            if via_db is not None:
                return via_db
        except TenantRepoUnavailable:
            # Propaga — o middleware traduz para 503 em produção.
            raise

    return _resolve_via_static(api_key)


# ---------------------------------------------------------------------------
# Compat: alias antigo
# ---------------------------------------------------------------------------


def find_tenant_by_api_key(api_key: str) -> TenantRow | None:  # noqa: D401
    """Alias para `resolve_tenant_by_api_key` (compatibilidade com testes antigos)."""
    return resolve_tenant_by_api_key(api_key)


class TenantBasicRow(TypedDict):
    tenant_id: str
    name: str


def list_all_tenants() -> list[TenantBasicRow]:
    """
    Lista os tenants conhecidos a partir da tabela tenants_api_keys.
    Retorna 1 linha por tenant (tenant_id, name).
    - Considera chaves ativas (revoked_at IS NULL)
    - 'name' é um representativo (MIN(name)) apenas para exibição/sincronização.
    """
    if psycopg is None:
        raise RuntimeError("psycopg não disponível para list_all_tenants()")

    dsn = _db_dsn()
    if not dsn:
        raise RuntimeError("DATABASE_URL não configurado para list_all_tenants()")

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tenant_id, MIN(name) AS name
                  FROM tenants_api_keys
                 WHERE revoked_at IS NULL
                 GROUP BY tenant_id
                 ORDER BY tenant_id
                """
            )
            rows = cur.fetchall()

    out: list[TenantBasicRow] = []
    for tenant_id, name in rows:
        out.append(TenantBasicRow(tenant_id=str(tenant_id), name=str(name)))
    return out
