import logging
import os

import psycopg

from .tenant_context import TenantInfo

logger = logging.getLogger("tenant_repo")

DSN = (
    os.getenv("DATABASE_URL")
    or os.getenv("DB_URL")
    or "postgresql://postgres:postgres@localhost:5432/friday_agents"
)


class TenantRepoUnavailable(Exception):
    pass


def find_tenant_by_api_key(api_key: str) -> TenantInfo | None:
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
