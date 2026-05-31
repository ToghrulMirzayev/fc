# FitnessCourt

> **Codename only.** This is a working name through v1.0. The product name lives in `.env` as `APP_NAME` and in `backend/app/branding/` (Python) and `frontend/src/lib/branding.ts` (TS). Change it in those places to rebrand the whole platform.

Multi-tenant SaaS for gyms and fitness studios. Memberships, check-ins, manual billing, member self-service via Telegram bot.

## What ships in v1.0

- **Admin Web** (Next.js 14) — gym owners, managers, receptionists manage everything here
- **Backend API** (FastAPI) — all business logic
- **Telegram Bot** — the only member-facing client in v1.0. Members link via one-time code, see their plan, get a **rotating QR code** for check-in
- **PostgreSQL + Redis** — data + cache + QR nonce store + Celery broker
- **Celery worker + beat** — scheduled jobs (skeleton; jobs land in Sprint 3)

## Quick start

```bash
# 1. Copy env, generate secrets
cp .env.example .env
# Edit .env — at minimum, set SECRET_KEY and QR_SIGNING_KEY:
#   openssl rand -hex 32
# Both should be at least 32 chars.

# 2. Bring up the stack
docker compose up --build

# 3. In another terminal — run migrations and seed demo data
docker compose exec api alembic upgrade head
docker compose exec api python -m app.scripts.seed_dev
docker compose exec api python -m app.scripts.seed_plans

# 4. Open the admin
#    http://localhost:3000/login
#    Email:    anna@iron.gym
#    Password: password123
```

The seed script creates one tenant ("Iron Gym"), one owner, four plans, twelve members with varied statuses, fifty historical visits, and a few payments. Enough to make every screen come alive.

## Telegram bot (local dev)

The bot uses webhooks, so it needs a public HTTPS URL.

1. Create a bot with [@BotFather](https://t.me/BotFather), copy the token.
2. Set `TELEGRAM_BOT_TOKEN` and a random `TELEGRAM_WEBHOOK_SECRET` in `.env`.
3. Start a tunnel: `cloudflared tunnel --url http://localhost:8000` or `ngrok http 8000`.
4. Set `TELEGRAM_WEBHOOK_URL=<tunnel>/bot/webhook` in `.env`, restart the api service.
5. Register the webhook (one-time, manually):

```bash
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -d "url=${TELEGRAM_WEBHOOK_URL}" \
  -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}"
```

6. To link a member to Telegram: go to their profile in the admin, hit "Generate linking code", give the 6-digit code to the member, and ask them to send it to your bot. The bot binds their Telegram user ID, and `/start` afterwards shows the menu.

If you don't have a Telegram bot, everything else works — the member-facing flow is just inaccessible.

## Project layout

```
backend/
  app/
    api/v1/      HTTP endpoints (auth, dashboard, members, operations)
    bot/         Telegram bot (aiogram handlers + webhook)
    branding/    Product name + bot copy. Rebrand here.
    core/        config, security, deps, tenant, logging, redis
    db/          SQLAlchemy session + base
    models/      SQLAlchemy ORM models
    schemas/     Pydantic request/response schemas
    services/    Business logic (auth, member, freeze, checkin, linking, qr_image)
    tasks/       Celery app
    scripts/     Dev helpers (seed_dev)
  alembic/       DB migrations

frontend/
  src/
    app/         Next.js App Router pages
      login/         Standalone (no AppShell)
      page.tsx       Dashboard
      members/       List + profile
      checkins/      Scanner + live feed
      plans/         Catalog + create
      [+ placeholders for bookings, payments, schedule, notifications, configuration]
    components/  AppShell, Sidebar, PageHeader, KpiCard, Panel, ExpiringList, ...
    lib/         api.ts, branding.ts, useAuth.ts

docs/
  MANIFESTO.md   Product manifesto
  ARCHITECTURE.md
  ROADMAP.md
  TELEGRAM_BOT.md
  FOLDERS.md
  adr/           Architecture decision records
  design/        mockup.html (designer's source of truth)
```

## Key docs

- [`docs/MANIFESTO.md`](docs/MANIFESTO.md) — product manifesto (source of truth for what we build)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — stack, decisions, why
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — sprint plan
- [`docs/design/mockup.html`](docs/design/mockup.html) — full design mockup
- [`docs/adr/`](docs/adr/) — ADRs

## Rebranding

1. Set `APP_NAME=YourName` in `.env`
2. Set `NEXT_PUBLIC_APP_NAME=YourName` in `.env`
3. Edit copy in `backend/app/branding/__init__.py` if needed
4. Edit copy in `frontend/src/lib/branding.ts` if needed

The brand mark itself (two angular strokes — see `frontend/src/components/Logo.tsx`) is decoupled from the name. To change it, edit `LogoMark` directly.

## What's NOT in v1.0

Deferred to v1.1+ per the manifesto:
- Stripe self-serve checkout (v1.0 uses manual payment marking)
- Mobile apps (Telegram bot covers member needs in v1.0)
- Member web portal (Telegram-only in v1.0)
- Class booking UI (backend models present, UI in Sprint 4)
- Postgres RLS (application-layer tenant isolation in v1.0)
- Prometheus / Grafana (Sentry + logs are enough at this scale)
- Kubernetes (Docker Compose on one VPS in v1.0)
