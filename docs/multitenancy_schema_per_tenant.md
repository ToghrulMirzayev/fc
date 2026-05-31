# Schema-per-tenant isolation

One Postgres database, two kinds of schema. Runs entirely inside the
existing `docker-compose.yml` — no extra services.

## Layout

- **`public` (control plane, shared):** `tenants`, `users`,
  `refresh_tokens`, `audit_log`, `discounts`, `signup_requests`,
  `feature_flags`. Who exists and what they may do.
- **`t_<slug>` (data plane, one per tenant):** `members`,
  `membership_plans`, `memberships`, `freeze_periods`, `visits`,
  `payments`. The client's actual data. `plan-basic` → schema `t_plan_basic`
  (hyphens become underscores).

The six data models declare a sentinel schema `tenant`. On every
authenticated request, `get_current_user` pins the DB connection to that
user's real schema via `schema_translate_map`, so the same query only ever
touches one client's schema. A client can never read another client's
members or payments — they are different tables in different schemas.

Enum types (e.g. `memberstatus`) live once in `public` and are referenced
cross-schema; they are not duplicated per tenant.

## Key files

- `app/db/tenancy.py` — sentinel name, slug→schema mapping.
- `app/db/provision.py` — `provision_tenant_schema()` / `drop_tenant_schema()`.
- `app/db/session.py` — `apply_tenant_schema()`, `tenant_session()`.
- `app/core/deps.py` — pins the schema after auth.
- `alembic/versions/0005_schema_per_tenant.py` — drops the old public data
  tables (control plane untouched, enums kept).

## Run it (Docker)

```bash
# 1. Rebuild & start
docker compose up -d --build

# 2. Apply migrations (creates control plane, drops old public data tables)
docker compose exec api alembic upgrade head

# 3. Seed: one company per plan tier, each in its own schema, one user each
docker compose exec api python -m app.scripts.seed_plans

# (or the single demo workspace)
docker compose exec api python -m app.scripts.seed_dev
```

If you have an existing dev volume with data in `public`, reset it first
(this wipes the DB):

```bash
docker compose down -v && docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python -m app.scripts.seed_plans
```

Log in at http://localhost:3000/login, password `demo12345`, e.g.
`basic@fitnesscourt.com`.

## Inspect schemas

```bash
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dn"
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "\dt t_plan_basic.*"
```

## Per-client backup / restore

Each client's data is one schema, so a backup contains only that client:

```bash
# Back up one client
./scripts/backup_tenant.sh plan-basic ./backups

# Restore one client (drops & reloads only their schema)
./scripts/restore_tenant.sh plan-basic ./backups/t_plan_basic-<ts>.sql
```

The dump references shared enum types in `public`, which exist on the same
server / any migrated DB. To move a client to a brand-new server, run
migrations there first so `public` has the enum types.

## Follow-ups (not done here)

- **Tenant activation endpoint:** when the super-admin panel activates a
  workspace, it must call `provision_tenant_schema(conn, slug)` before the
  owner logs in. (No activation endpoint exists yet.)
- **Telegram bot:** the bot looks up a member by `telegram_user_id`
  globally, which no longer works once members are per-schema. It needs a
  small shared `public` index (telegram_user_id → tenant) to resolve the
  tenant, then `tenant_session(slug)`. The bot is currently disabled (no
  token), so this is not yet wired.
