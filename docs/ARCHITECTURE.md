# Architecture

## What This Is

Fitness Court is a multi-tenant SaaS for gym operations: memberships, check-ins, manual billing, member self-service. v1.0 ships an admin web app for staff and a Telegram bot as the only member-facing client. Target: 50 gyms in the first 6–8 weeks. Solo dev.

## Assumptions

These were not specified by the user and I picked the conservative answer. **Confirm or override:**

- Geographic focus: RU/CIS-leaning early (because Telegram-first member experience is strongest there). Architecture is geo-agnostic, but bot copy and payment defaults assume this. → Confirm.
- Each member belongs to exactly one gym (tenant) in v1.0. Multi-gym membership (one phone number, multiple gyms) is deferred. → Confirm.
- Each staff user belongs to exactly one gym in v1.0. → Confirm.
- The Keybit team will operate as super admin and run the platform; gyms self-serve only within their tenant. → Confirm.
- Budget for v1.0 infra: under €20/mo. → Confirm.

## The Stack

| Layer | Pick | Why |
|---|---|---|
| Backend language | Python 3.12 | Manifesto specifies FastAPI; Python ecosystem covers aiogram (bot), Celery (jobs), SQLAlchemy (ORM) cleanly in one runtime. |
| API framework | FastAPI | Async, OpenAPI for free, Pydantic v2 validation, fits modular monolith. |
| ORM / DB toolkit | SQLAlchemy 2.x async + Alembic | Industry standard for Python. Async support is mature in 2.x. |
| Database | PostgreSQL 16 | Boring, proven, multi-tenant friendly. Hetzner provides it cheaply or we self-host in Docker. |
| Cache + broker | Redis 7 | Doubles as Celery broker, rate limit store, QR single-use tracker. |
| Background jobs | Celery + Celery Beat | Cron-like scheduling needed for freeze auto-resume, expiration reminders. Beat is more mature than RQ-Scheduler. |
| Telegram bot | aiogram 3.x | Webhook mode, runs inside the same FastAPI process. No separate service. |
| Frontend | Next.js 14 (App Router) + TypeScript | Manifesto choice. SSR for SEO on marketing pages, client-side for admin app. |
| UI | TailwindCSS + shadcn/ui | Fast to build, customizable, matches "minimal, operationally efficient" principle. |
| State (FE) | TanStack Query (server) + Zustand (client, sparingly) | TanStack handles 90% of state via server cache. Zustand for the small client-only bits (sidebars, modals). |
| Auth | Custom JWT (access + refresh) | Manifesto choice. No third-party auth provider — keeps tenant model fully in our control. Argon2id for password hashing. |
| Reverse proxy + TLS | Caddy 2 | One-line TLS via Let's Encrypt. Simpler than Nginx + certbot. |
| Container orchestration | Docker Compose | Right tool for one VPS. K8s is for later. |
| Hosting | Hetzner Cloud CX22 VPS (~€4.5/mo) | Cheapest reliable option. 2 vCPU / 4GB RAM / 40GB SSD covers 50 gyms with headroom. |
| File storage | Local volume (v1.0), Cloudflare R2 later | Avatars, invoice PDFs. No need for object storage until we add a second instance. |
| Backups | Daily `pg_dump` → Cloudflare R2 (free tier) | Free, durable, off-VPS. |
| Error tracking | Sentry (free tier) | Backend + frontend. |
| Uptime | UptimeRobot (free tier) hitting `/health` | Enough for one VPS. |
| CI/CD | GitHub Actions | Free for our scale. Lint, type-check, test, build images. |

## What I Considered and Rejected

- **Django instead of FastAPI** — rejected because manifesto specifies FastAPI and async is a better fit for the bot + API in one process.
- **NestJS / Node backend** — rejected because Python ecosystem for the bot (aiogram) and Celery is stronger; manifesto specifies Python anyway.
- **Supabase / Firebase for auth + DB** — rejected because tenant model with `tenant_id` filtering plus custom RBAC is awkward on top of their row-level security model, and we lose control over the schema migrations.
- **Managed cloud (Railway, Render, Fly.io)** — rejected because for €5/mo Hetzner gives 4–10x the resources of an equivalent managed plan. We have a solo dev who can run `docker compose up`; we don't need managed yet.
- **AWS / GCP** — rejected as overbuilt for 50 gyms. Egress costs and complexity not justified.
- **RQ instead of Celery** — rejected because we need cron-like scheduling for daily/hourly tasks; Celery Beat is more battle-tested for this than RQ-Scheduler.
- **Row-level security (RLS) in Postgres** — deferred. Application-layer `tenant_id` filtering with a SQLAlchemy event hook + tests covers v1.0 and is faster to build. Revisit when onboarding a customer that mandates DB-enforced isolation.
- **Microservices from day one** — rejected. Solo dev, 6–8 weeks. Modular monolith with clean boundaries is the right shape for this stage.
- **Stripe in v1.0** — deferred to v1.1 (see manifesto change log).
- **Separate process for the Telegram bot** — rejected. aiogram in webhook mode is one POST endpoint inside the FastAPI app. Sharing the app gives the bot direct access to services and the DB session with no IPC.

## High-Level Architecture

```
                   Cloudflare DNS (*.fitnesscourt.com)
                              │
                              ▼
                       ┌─────────────┐
                       │   Caddy 2   │  ← TLS, reverse proxy
                       └──────┬──────┘
                              │
              ┌───────────────┼───────────────────┐
              ▼               ▼                   ▼
       ┌──────────┐    ┌──────────────────────────────┐
       │ Next.js  │    │           FastAPI            │
       │ admin web│    │  ┌────────┬────────┬──────┐  │
       │  :3000   │    │  │ /api/v1│ /bot/  │/health│ │
       └──────────┘    │  └────────┴────────┴──────┘  │
                       │   aiogram (webhook) inside   │
                       │           same app           │
                       └──────┬───────────────┬───────┘
                              │               │
                       ┌──────▼─────┐   ┌─────▼──────┐
                       │ PostgreSQL │   │   Redis    │
                       │     16     │   │  (cache +  │
                       │            │   │  broker +  │
                       └──────┬─────┘   │ QR tokens) │
                              │         └─────┬──────┘
                              │               │
                       ┌──────▼───────────────▼──────┐
                       │  Celery worker + Celery beat │
                       │  (same image, different cmd) │
                       └──────────────────────────────┘

  All services run on one Hetzner VPS via Docker Compose.
  Telegram → Caddy → /bot/webhook → aiogram handlers → services → DB
  Admin web → /api/v1/* → FastAPI routes → services → DB
```

## Key Decisions (ADR-lite)

- **Modular monolith, not microservices.** One Python codebase, clean module boundaries (`auth`, `tenants`, `memberships`, `checkins`, `crm`, `billing`, `bot`, `notifications`). Splitting is reversible later; premature splitting is expensive now.
- **Tenant isolation at the application layer.** Every tenant-scoped query passes through a base repository that injects `tenant_id` from request context. Enforced by tests. Postgres RLS deferred.
- **Telegram bot lives inside the API process.** Webhook mode, one POST endpoint. No separate deployable, no IPC.
- **Rotating QR codes.** QR encodes a short-lived (default 30s) HMAC-signed token. Single-use tracked in Redis with TTL. Static QR explicitly rejected as a security hole. Bot regenerates QR on demand; scanner endpoint validates and burns the token.
- **Subdomain-based tenant routing.** `iron.fitnesscourt.com` resolves tenant from subdomain at the middleware layer. API also accepts `X-Tenant-Slug` header for non-browser clients (the bot).
- **Manual billing in v1.0.** Stripe is 1.5–2 weeks of work that 80% of early gyms don't need. Defer.
- **Codename strategy.** `APP_NAME` env var + `app/branding/strings.py` (backend) + `frontend/src/lib/branding.ts`. All user-facing strings flow through these. Rebrand = edit two files.
- **JWT for staff, Telegram user ID for members.** Members authenticate to the bot by linking their Telegram ID to a member record via a one-time code (staff generates it from admin web). No passwords for members.
- **Async SQLAlchemy throughout.** Mixing sync and async drivers is a footgun. All DB code is async.
- **Database migrations via Alembic with autogenerate, but every migration is reviewed by hand.** Autogenerate is a draft, not a commit.

## What This Architecture Will NOT Do (yet)

- Will not survive the single VPS going down. v1.0 has no HA. Acceptable risk for 50 gyms in early access.
- Will not handle 1000+ gyms on one box. Scaling path is documented in the manifesto.
- Will not do per-row encryption, HSM-backed keys, or any heavyweight crypto. Standard at-rest disk encryption + TLS in transit + Argon2id for passwords is the baseline.
- Will not have multi-region failover.
- Will not have a separate microservice for any module.
- Will not have GraphQL.
- Will not have a service mesh, distributed tracing, or APM. Sentry + logs cover us.
- Will not have feature flags infra. If we need a flag, it goes in `tenants` config.

## When to Revisit

Trigger an architecture review if any of these hit:

- **300+ active gyms** — start thinking about splitting DB to managed and adding a second app instance.
- **Sustained >70% CPU or >80% RAM on the VPS** — vertical scale first (CX32 → CX42), then horizontal.
- **First enterprise customer demands DB-level tenant isolation** — implement Postgres RLS.
- **Stripe webhooks need to scale past one process** — split billing into its own worker.
- **Telegram bot traffic dominates the API process and degrades admin web latency** — extract the bot into its own deployable.
- **We hire a second backend dev** — revisit module boundaries; what was clean enough for solo dev may need formal interfaces.
- **A real outage from single-VPS failure costs more than €100/mo of HA infra** — move to managed services.

## Threat model (lightweight, v1.0)

- **Account takeover (staff)** — mitigated by Argon2id, refresh rotation, rate limit on `/auth/login`, audit log on auth events. 2FA in v1.1.
- **QR replay** — single-use token in Redis with TTL. Even with a leaked screenshot, the window is ~30s and the token can be used once.
- **Cross-tenant data leak** — caught by integration tests that assert tenant scoping. Every list endpoint has a test that creates two tenants and verifies isolation.
- **Telegram bot impersonation** — bot validates webhook signature (`X-Telegram-Bot-Api-Secret-Token`). Account linking codes are single-use and expire in 10 minutes.
- **Storage abuse** — file uploads (avatars only in v1.0) capped at 2MB, type-checked.
- **VPS compromise** — daily off-VPS backups to R2. Disk encryption on at rest. SSH key only, no password.

## Performance budget (target for v1.0)

- API P95 latency: < 300ms for read endpoints, < 600ms for writes
- QR generation in bot: < 200ms perceived
- Check-in scan to response: < 400ms (this is what receptionists feel)
- Admin web initial load: < 2s on 4G

These are targets, not promises. Measured via Sentry performance + manual k6 runs before launch.
