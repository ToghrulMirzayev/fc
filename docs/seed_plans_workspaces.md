# Demo workspaces по тарифам (seed_plans)

Сид `backend/app/scripts/seed_plans.py` создаёт по одной компании (тенанту) на каждый тариф.

**Запуск:** `docker compose exec api python -m app.scripts.seed_plans` (идемпотентный — сначала чистит эти тенанты)

**Вход:** http://localhost:3000/login · пароль у всех — `demo12345`

## Workspaces

| Тариф | Slug | Название workspace | Логин (email) | Цена | Members (seed) | Открытые feature-гейты |
|---|---|---|---|---|---|---|
| FREE | `plan-free` | Trial Gym (Trial plan) | free@fitnesscourt.com | €0/mo | 6 | — (только базовые) |
| BASIC | `plan-basic` | Starter Gym (Starter plan) | basic@fitnesscourt.com | €49/mo | 10 | — (только базовые) |
| ADVANCED | `plan-advanced` | Growth Gym (Growth plan) | advanced@fitnesscourt.com | €99/mo | 16 | bookings, telegram_automation, analytics |
| PRO | `plan-pro` | Pro Gym (Pro plan) | pro@fitnesscourt.com | €199/mo | 24 | bookings, telegram_automation, analytics, ai_insights, access_control |
| PREMIUM | `plan-premium` | Premium Gym (Premium plan) | premium@fitnesscourt.com | €399/mo | 30 | bookings, telegram_automation, analytics, ai_insights, access_control |
| CORPORATE | `plan-corporate` | Corporate Gym (Corporate plan) | corporate@fitnesscourt.com | custom | 36 | bookings, telegram_automation, analytics, ai_insights, access_control |

> Базовые секции (dashboard, members, checkins, plans, payments, configuration) включены у всех тарифов. В колонке «Открытые feature-гейты» — только дополнительно разблокированные платные фичи.

## Что создаётся в каждом workspace

| Сущность | Детали |
|---|---|
| Tenant | slug `plan-<tier>`, валюта AZN, активный (вход работает) |
| Owner | `<tier>@fitnesscourt.com` / пароль `demo12345`, роль OWNER |
| Membership-планы | Monthly Unlimited (80), 10-visit pack (60), Yearly Premium (800), Trial 7-day (0) |
| Members | кол-во по таблице выше, ~15% «ожидают оплату» (INACTIVE), остальные ACTIVE |
| Memberships | по абонементу на участника, со сроками, остатком визитов и статусом оплаты |
| Visits | ~4 визита на участника за последние 14 дней (только оплаченные) |
| Payments | по платежу на каждого оплаченного участника (CASH) |
| Feature flags | 5 платных гейтов вкл/выкл согласно тарифу |
| SignupRequest | с `interested_tier` — компания видна под своим планом в супер-админке |

## Тарифные лимиты (из `billing_plans.py`)

| Тариф | Member cap | Admin seats | Locations |
|---|---|---|---|
| FREE | 50 | 1 | 1 |
| BASIC | 200 | 2 | 1 |
| ADVANCED | 600 | 5 | 2 |
| PRO | 2000 | 15 | 5 |
| PREMIUM | 6000 | 40 | 15 |
| CORPORATE | ∞ | ∞ | ∞ |
