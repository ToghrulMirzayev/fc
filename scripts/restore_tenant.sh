#!/usr/bin/env bash
#
# Restore ONE tenant's data from a backup produced by backup_tenant.sh.
#
# Drops the tenant's schema and reloads it from the dump. Other tenants and
# the control plane (public schema) are untouched. The dump references the
# shared enum types in "public", which must already exist in the target DB
# (they do on the same server / a migrated DB).
#
# Usage:
#   ./scripts/restore_tenant.sh <slug> <backup_file.sql>
# Example:
#   ./scripts/restore_tenant.sh plan-basic ./backups/t_plan_basic-20260531-120000.sql
#
set -euo pipefail

slug="${1:?usage: restore_tenant.sh <slug> <backup_file.sql>}"
file="${2:?usage: restore_tenant.sh <slug> <backup_file.sql>}"

if [[ ! -f "$file" ]]; then
  echo "Backup file not found: $file" >&2
  exit 1
fi

if [[ -f .env ]]; then
  set -a; source .env; set +a
fi
db_user="${POSTGRES_USER:-postgres}"
db_name="${POSTGRES_DB:-fitnesscourt}"
schema="t_${slug//-/_}"

echo "Dropping schema ${schema} (if any) and restoring from ${file}..."
docker compose exec -T db psql -U "$db_user" -d "$db_name" \
  -c "DROP SCHEMA IF EXISTS \"${schema}\" CASCADE;"
docker compose exec -T db psql -U "$db_user" -d "$db_name" < "$file"

echo "Restored ${schema}."
