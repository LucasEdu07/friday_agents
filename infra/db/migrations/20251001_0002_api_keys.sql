CREATE TABLE IF NOT EXISTS tenants_api_keys (
    id              TEXT PRIMARY KEY,
    tenant_id       TEXT NOT NULL,
    name            TEXT NOT NULL,
    algo            TEXT NOT NULL,
    iterations      INTEGER NOT NULL,
    salt_b64        TEXT NOT NULL,
    hash_b64        TEXT NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at      TIMESTAMP NULL,
    last_used_at    TIMESTAMP NULL,
    UNIQUE (tenant_id, name, revoked_at)
);

CREATE INDEX IF NOT EXISTS idx_api_keys_tenant_active
  ON tenants_api_keys(tenant_id)
  WHERE revoked_at IS NULL;
