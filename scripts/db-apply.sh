#!/usr/bin/env bash
set -euo pipefail

: "${DB_URL:=}"

if [[ -z "$DB_URL" ]]; then
  echo "Defina DB_URL. Exemplos:"
  echo "  export DB_URL=sqlite:///./dev.db"
  echo "  export DB_URL=postgres://user:pass@localhost:5432/friday_agents"
  exit 1
fi

MIG="infra/db/migrations/20250922_0001_create_tenants.sql"

if [[ "$DB_URL" == sqlite:* ]]; then
  FILE="${DB_URL#sqlite:///}"
  mkdir -p "$(dirname "$FILE")"
  sqlite3 "$FILE" < "$MIG"
  echo "Migração aplicada em SQLite: $FILE"
else
  # Postgres
  psql "$DB_URL" -f "$MIG"
  echo "Migração aplicada em Postgres: $DB_URL"
fi
