# Folder Map

One-line description of what goes where. Keep this updated when you add a top-level folder.

## `backend/`

| Path | What goes here |
|---|---|
| `app/api/v1/` | FastAPI routers, one file per resource (`auth.py`, `members.py`, `memberships.py`, ...). Thin — calls into `services/`. |
| `app/bot/` | aiogram handlers + the webhook route. The bot is a module of the API app, not a separate process. |
| `app/branding/` | All product-name strings + bot copy + email subjects. Rebrand = edit here. |
| `app/core/` | Cross-cutting concerns: `config.py` (settings), `security.py` (JWT, hashing), `logging.py`, `deps.py` (FastAPI dependencies like `get_current_user`), `tenant.py` (tenant middleware + context). |
| `app/db/` | `session.py` (engine + session factory), `base.py` (declarative base + mixins). No business logic. |
| `app/models/` | SQLAlchemy ORM models, one file per aggregate (`tenant.py`, `member.py`, `membership.py`, ...). |
| `app/schemas/` | Pydantic request/response schemas, mirrors `models/`. |
| `app/services/` | Business logic. Pure functions or service classes that take a session + inputs and return domain objects. **No HTTP, no DB session creation — those come from callers.** |
| `app/tasks/` | Celery tasks + Celery app config (`celery_app.py`). Tasks delegate to `services/`. |
| `alembic/` | DB migrations. Every migration reviewed by hand before merge. |
| `tests/` | pytest tests. Mirror `app/` structure. Integration tests in `tests/integration/`. |

## `frontend/`

| Path | What goes here |
|---|---|
| `src/app/` | Next.js App Router pages and layouts. |
| `src/components/` | Reusable React components. shadcn/ui-style organization. |
| `src/hooks/` | Custom React hooks (mostly TanStack Query wrappers). |
| `src/lib/` | Pure utilities: `branding.ts`, `api-client.ts`, `auth.ts`. No React. |

## `docs/`

Authoritative project documentation. PRs that change behavior should update relevant doc in the same PR.

## `docker/`

Production Dockerfiles, Caddy config for prod, compose overrides for staging/prod.

## `scripts/`

Operational scripts: deploy, db backup/restore, dev helpers. Bash + Python only.

## What does NOT have a folder yet

- `infra/` (Terraform/Pulumi) — not needed at v1.0 scale.
- `packages/` (monorepo) — single-repo is fine, no monorepo tooling needed.
- `mobile/` — v2.0.
