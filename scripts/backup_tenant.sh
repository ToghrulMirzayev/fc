#!/usr/bin/env bash
#
# Back up ONE tenant's data — and nothing else.
#
# Each tenant's domain data lives in its own Postgres schema "t_<slug>"
# (members, plans, memberships, visits, payments). This dumps exactly that
# schema, so the resulting file contains only the requesting client's data.
#
# Usage:
#   ./scripts/backup_tenant.sh <slug> [output_dir]
# Example:
#   ./scripts/backup_tenant.sh plan-basic ./backups
#
set -euo pipefail

slug="${1:?usage: backup_tenant.sh <slug> [output_dir]}"
out_dir="${2:-./backups}"

# Load DB credentials from .env if present.
if [[ -f .env ]]; then
  set -a; source .env; set +a
fi
db_user="${POSTGRES_USER:-postgres}"
db_name="${POSTGRES_DB:-fitnesscourt}"

# Slug -> schema name (hyphens become underscores; matches schema_for_slug).
schema="t_${slug//-/_}"
ts="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$out_dir"
out="${out_dir%/}/${schema}-${ts}.sql"

echo "Dumping schema ${schema} from ${db_name}..."
docker compose exec -T db pg_dump \
  -U "$db_user" -d "$db_name" \
  --schema="$schema" --no-owner --no-privileges \
  > "$out"

echo "Wrote $out"
