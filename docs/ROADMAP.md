# Roadmap

## Definition of MVP

**v1.0 MVP = a gym owner can run their gym on it.**

Concretely, one gym should be able to:
- onboard staff users
- create membership plans
- register members
- have members link Telegram bot to their account
- generate rotating QR codes via the bot for members
- check members in by scanning QR
- view who's active / expired / frozen
- mark payments manually
- get expiration reminders to members via Telegram

Core happy path that has to work end-to-end before launch:

> A new member walks in → receptionist creates their profile and plan → member scans the staff-provided code in Telegram to link account → member opens bot → taps "Show QR" → presents to scanner → check-in is recorded → member sees updated visits remaining in bot.

Anything that doesn't serve this path is cut from v1.0 unless explicitly scheduled below.

---

## Sprint 0 — Foundation (week 1)

Goal: dev can clone, run, deploy. CI is green. Auth + tenant scaffolding works.

- [x] Repo initialized, ARCHITECTURE.md and MANIFESTO.md committed
- [x] Folder structure created
- [ ] `docker-compose.dev.yml` brings up Postgres + Redis + API + frontend locally — Done means: `docker compose up` from a fresh clone and both http://localhost:8000/docs and http://localhost:3000 respond
- [ ] FastAPI skeleton: health check, settings via pydantic-settings, structured logging — Done means: `/health` returns 200 with version, logs are JSON
- [ ] Alembic configured, first migration: `tenants`, `users`, `roles`, `audit_log` tables — Done means: `alembic upgrade head` succeeds on empty DB
- [ ] Auth module: register (super-admin-only), login, refresh, password reset request — Done means: pytest covers happy path + bad password + expired token
- [ ] Tenant middleware: resolves `tenant_id` from subdomain OR `X-Tenant-Slug` header OR JWT claim — Done means: test asserts cross-tenant access returns 404
- [ ] Next.js scaffold: shadcn/ui installed, login page, authenticated layout, route guard — Done means: can log in against backend and see a placeholder dashboard
- [ ] GitHub Actions: lint (ruff, eslint), type-check (mypy, tsc), test (pytest, vitest), build images — Done means: CI runs on PR and is green
- [ ] Sentry wired up on backend and frontend (DSN via env, no-op if empty) — Done means: a manually thrown error appears in Sentry test project
- [ ] Branding module exists (`backend/app/branding/strings.py`, `frontend/src/lib/branding.ts`) and is used for every user-facing string in the auth flow — Done means: changing `APP_NAME` env updates login page title

**Decisions needed before starting:** none. All clarified.

---

## Sprint 1 — Memberships + CRM (weeks 2–3)

Goal: gym staff can fully manage members and plans from admin web. Core business logic shipped.

- [ ] DB schema: `branches`, `membership_plans`, `memberships`, `members`, `freeze_periods` — Done means: migration applied, model unit tests pass
- [ ] Membership plan CRUD (API + admin UI) — types: unlimited monthly, limited-visits, yearly, trial, one-time — Done means: can create each plan type and see it in the list
- [ ] Member CRUD (API + admin UI) — Done means: can register member with phone + name, see them in member list, search by name/phone
- [ ] Assign plan to member, set start/end dates — Done means: member detail page shows active plan, days remaining, visits remaining
- [ ] Freeze workflow (admin-initiated only in v1.0): pause, resume, auto-resume by date — Done means: frozen member shows correct status, plan resumes correctly, audit log records action
- [ ] Member status computation (active/frozen/expired/inactive) — Done means: status derived from data, not stored; tests cover boundary cases (last day of plan, etc.)
- [ ] Member notes + tags — Done means: staff can add a note, filter member list by tag
- [ ] Tenant isolation integration tests — Done means: test creates two tenants, asserts every list endpoint scopes correctly

**Decisions needed before starting:**
- Confirm phone number is the unique key for members within a tenant (Telegram linking happens via phone).

---

## Sprint 2 — Telegram Bot + QR Check-in (weeks 3–4)

Goal: members can link their Telegram, see their plan, and check in via rotating QR. Receptionists can scan.

- [ ] aiogram 3.x wired into FastAPI app via webhook — Done means: bot responds to `/start` in dev (using ngrok/cloudflared tunnel)
- [ ] Account linking flow: admin generates one-time code for a member → member sends code to bot → bot binds Telegram ID to member — Done means: linked member sees "Welcome, {name}" with their plan info on `/start`
- [ ] Bot main menu: My Plan, Show QR, Visit History, Help — Done means: each option returns correct data scoped to that member's tenant
- [ ] QR generation service: HMAC-signed token, 30s TTL, single-use tracked in Redis — Done means: unit tests cover signing, expiry, replay
- [ ] Bot "Show QR" command: returns QR image with rotating token, refreshes on demand — Done means: scanning the same QR twice within 30s = second scan rejected
- [ ] Check-in endpoint: receives token, validates, records visit, decrements visits if limited plan, returns member info — Done means: end-to-end check-in works, audit log records, occupancy counter updates
- [ ] Receptionist scanner page in admin web: camera-based QR scan (HTML5 QR scanner) OR keyboard wedge scanner support — Done means: scanning a member's QR shows their name + plan + check-in confirmation
- [ ] Manual check-in path for staff (search member, click "Check in") — Done means: visit recorded with `method=manual` flag
- [ ] Anti-passback: configurable cooldown between consecutive check-ins by same member — Done means: second check-in within cooldown is rejected with clear message
- [ ] Bot copy lives in branding module, RU + EN — Done means: switching `APP_LOCALE` changes bot replies

**Decisions needed before starting:**
- Confirm QR TTL of 30s. Trade-off: shorter = more secure + worse UX if scanner is slow; longer = better UX + slightly bigger replay window.
- Decide on the QR scanner hardware assumption (phone camera in admin web vs USB scanner) — affects UX of the scanner page.

---

## Sprint 3 — Manual Billing + Notifications + Analytics (weeks 5–6)

Goal: gyms can record payments, members get reminders, owner sees a useful dashboard.

- [ ] Payment model: link to member, amount, currency, method (cash/transfer/card_external), date, plan being paid for — Done means: payments listed on member profile, payment history page exists
- [ ] Invoice PDF generation (Celery task) — Done means: invoice attached to payment, downloadable from admin web, sent to member's Telegram
- [ ] Renewal reminder Celery beat task: runs daily, finds plans expiring in 7/3/1 days, sends Telegram message — Done means: test member with plan expiring tomorrow receives reminder
- [ ] Freeze expiration reminder: notifies member 1 day before auto-resume — Done means: same as above
- [ ] Email transactional sends (via Resend or Mailgun free tier) — Done means: password reset email arrives
- [ ] Owner dashboard: active members count, this month's revenue (manual), check-ins per day chart, expiring this week list — Done means: dashboard loads in < 2s, numbers reconcile with raw DB queries
- [ ] Daily analytics rollup Celery beat task: writes pre-aggregated daily stats to a table — Done means: dashboard reads from rollup, not from raw events

**Decisions needed before starting:**
- Pick email provider. Recommendation: Resend (3000 emails/mo free, dead-simple API).
- Confirm currency is per-tenant (each gym configures its currency once) vs global.

---

## Sprint 4 — Booking + Production Launch (weeks 7–8)

Goal: optional booking module shipped, production deployment hardened, first real gym onboarded.

- [ ] Class scheduling (API + admin UI): trainers, recurring slots, capacity — Done means: a class series can be created and listed
- [ ] Member can book a class via Telegram bot — Done means: bot shows upcoming classes, member can reserve, sees confirmation
- [ ] Waiting list when class full — Done means: when a spot opens, next on list is auto-notified
- [ ] Cancellation policy enforcement (configurable hours before class) — Done means: cancelling within window rejected with clear message
- [ ] Production deploy: Hetzner VPS provisioned, Caddy, Docker Compose, daily backups to R2, UptimeRobot monitoring — Done means: `fitnesscourt.com` resolves, TLS valid, `/health` returns green, backup ran last night
- [ ] Production runbook in `docs/RUNBOOK.md`: how to deploy, how to rollback, how to restore from backup, how to read logs — Done means: a second person could deploy from the runbook alone
- [ ] Load smoke test with k6: 100 RPS sustained for 5 min, P95 latency under target — Done means: results documented in `docs/PERFORMANCE.md`
- [ ] First real gym onboarded as pilot — Done means: their staff is using the system live for at least 3 days

**Decisions needed before starting:**
- If timeline slips by week 6, booking is cut from v1.0 to v1.1. Production launch is non-negotiable.

---

## Backlog (not scheduled yet)

- Member-initiated freeze request (currently admin-only)
- Bulk member import (CSV)
- Multi-branch support per gym (currently every gym = 1 branch logically; model supports multi-branch but UI doesn't)
- Trainer-side views (their classes, their members)
- 2FA for staff accounts
- Webhook outbound (for integration with external systems)
- Public REST API tokens for integration partners
- Reporting export (CSV/Excel)
- White-label theming per tenant beyond global brand
- Member-facing web portal (only if Telegram proves insufficient)

---

## Explicitly Deferred (post-v1.0)

- **Stripe / online payments** — manual billing covers v1.0; Stripe is v1.1
- **Mobile apps** — v2.0+; Telegram bot covers v1.0
- **Member web portal** — Telegram bot is the member surface in v1.0
- **AI features** — not in roadmap
- **Workout / nutrition tracking** — not in roadmap
- **Smartwatch / wearable integrations** — not in roadmap
- **Marketplace / social features** — not in roadmap
- **Postgres RLS** — application-layer isolation in v1.0
- **Prometheus / Grafana** — Sentry + logs in v1.0
- **Kubernetes** — Docker Compose on one VPS in v1.0
- **Microservices** — modular monolith in v1.0
- **RFID / facial recognition check-in** — QR-only in v1.0
- **WhatsApp / SMS / push notifications** — Telegram + email only in v1.0

---

## Risks to the timeline

- **Telegram bot complexity underestimated** — aiogram is straightforward but webhook + dev tunneling has friction. Mitigation: Sprint 2 starts with a 1-day spike to prove the webhook flow before building real handlers.
- **QR rotation UX feels janky on slow networks** — Mitigation: 30s TTL is a setting, tune in pilot.
- **Solo dev burnout** — 8 weeks at the planned pace is tight. Mitigation: booking module (Sprint 4) is the explicit cut line if Sprint 1-3 take longer.
- **Tenant isolation bug in production** — Mitigation: integration tests are non-negotiable in Sprint 0/1; every list endpoint gets a multi-tenant test.

---

## Next Step

Sprint 0 starts now. First concrete task: bring up `docker-compose.dev.yml` and prove `/health` returns 200 from a fresh clone. Files for that are scaffolded in this repo init — verify locally and start filling in the auth module.
