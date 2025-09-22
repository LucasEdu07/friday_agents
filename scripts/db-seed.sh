#!/usr/bin/env bash
set -euo pipefail

: "${DB_URL:=}"

SEED="infra/db/seeds/20250922_seed_tenants.sql"

if [[ "$DB_URL" == sqlite:* ]]; then
  FILE="${DB_URL#sqlite:///}"
  sqlite3 "$FILE" < "$SEED"
  echo "Seed aplicada em SQLite: $FILE"
else
  psql "$DB_URL" -f "$SEED"
  echo "Seed aplicada em Postgres: $DB_URL"
fi
