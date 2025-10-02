from __future__ import annotations

import base64
import hashlib
import os
import time
import uuid
from dataclasses import dataclass

import psycopg


@dataclass(frozen=True)
class ApiKeyRow:
    id: str
    tenant_id: str
    name: str
    algo: str
    iterations: int
    salt_b64: str
    hash_b64: str
    revoked_at: float | None  # epoch seconds | None
    created_at: float | None  # opcional, não usamos aqui


# ————————————————————————————————————————————————————————————————————————
# Low-level: conexão
# ————————————————————————————————————————————————————————————————————————


def _dsn() -> str:
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL não configurado")
    return dsn


# ————————————————————————————————————————————————————————————————————————
# Crypto util (PBKDF2-SHA256) — compatível com seus aceites
# ————————————————————————————————————————————————————————————————————————

_PBKDF2_ALGO = "pbkdf2_sha256"
_PBKDF2_ITER = int(os.getenv("API_KEY_ITERATIONS", "120000"))


def _derive(api_key_plain: bytes, *, iterations: int = _PBKDF2_ITER) -> tuple[str, str, int]:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", api_key_plain, salt, iterations, dklen=32)
    return base64.b64encode(salt).decode(), base64.b64encode(dk).decode(), iterations


# ————————————————————————————————————————————————————————————————————————
# Queries
# ————————————————————————————————————————————————————————————————————————


def list_keys(tenant_id: str) -> list[ApiKeyRow]:
    with psycopg.connect(_dsn()) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, tenant_id, name, algo, iterations, salt_b64, hash_b64,
                   EXTRACT(EPOCH FROM revoked_at), EXTRACT(EPOCH FROM created_at)
              FROM tenants_api_keys
             WHERE tenant_id = %s
             ORDER BY created_at DESC
            """,
            (tenant_id,),
        )
        rows = cur.fetchall()

    out: list[ApiKeyRow] = []
    for r in rows:
        out.append(
            ApiKeyRow(
                id=str(r[0]),
                tenant_id=str(r[1]),
                name=str(r[2]),
                algo=str(r[3]),
                iterations=int(r[4]),
                salt_b64=str(r[5]),
                hash_b64=str(r[6]),
                revoked_at=(float(r[7]) if r[7] is not None else None),
                created_at=(float(r[8]) if r[8] is not None else None),
            )
        )
    return out


def _insert_key(tenant_id: str, name: str, api_key_plain: str) -> None:
    salt_b64, hash_b64, iterations = _derive(api_key_plain.encode("utf-8"))
    with psycopg.connect(_dsn()) as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO tenants_api_keys
                (id, tenant_id, name, algo, iterations, salt_b64, hash_b64)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(uuid.uuid4()),
                tenant_id,
                name,
                _PBKDF2_ALGO,
                iterations,
                salt_b64,
                hash_b64,
            ),
        )
        conn.commit()


def create_key(tenant_id: str, *, name: str | None = None) -> tuple[str, str]:
    """
    Cria **nova** chave ativa para o tenant.
    Retorna (name, api_key_plain).
    - Banco persiste apenas hash/salt.
    - Logs não devem expor a chave.
    """
    # nome amigável default
    name = name or f"key-{int(time.time())}"

    # gera um segredo forte (não previsível)
    api_key_plain = base64.urlsafe_b64encode(os.urandom(24)).decode().rstrip("=")

    _insert_key(tenant_id, name, api_key_plain)
    return name, api_key_plain


def revoke_key(tenant_id: str, name: str) -> int:
    """
    Revoga a chave (marca revoked_at = now()).
    Retorna número de linhas afetadas (0|1).
    """
    with psycopg.connect(_dsn()) as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE tenants_api_keys
               SET revoked_at = NOW()
             WHERE tenant_id = %s
               AND name = %s
               AND revoked_at IS NULL
            """,
            (tenant_id, name),
        )
        n = cur.rowcount
        conn.commit()
    return int(n)


def rotate_key(
    tenant_id: str,
    *,
    previous_name: str | None = None,
    new_name: str | None = None,
) -> tuple[str, str]:
    """
    Rotaciona chave:

      - revoga a anterior (se `previous_name` informado, tenta essa; se não,
        revoga a mais nova ativa)
      - cria nova (retorna (new_name, new_api_key_plain))
    """
    # 1) Revogar anterior
    with psycopg.connect(_dsn()) as conn, conn.cursor() as cur:
        if previous_name:
            cur.execute(
                """
                UPDATE tenants_api_keys
                   SET revoked_at = NOW()
                 WHERE tenant_id = %s
                   AND name = %s
                   AND revoked_at IS NULL
                """,
                (tenant_id, previous_name),
            )
        else:
            # revoga a mais nova ativa
            cur.execute(
                """
                UPDATE tenants_api_keys
                   SET revoked_at = NOW()
                 WHERE id = (
                    SELECT id
                      FROM tenants_api_keys
                     WHERE tenant_id = %s AND revoked_at IS NULL
                     ORDER BY created_at DESC
                     LIMIT 1
                 )
                """,
                (tenant_id,),
            )
        conn.commit()

    # 2) Criar nova
    new_name = new_name or f"key-{int(time.time())}"
    name, api_key_plain = create_key(tenant_id, name=new_name)
    return name, api_key_plain
