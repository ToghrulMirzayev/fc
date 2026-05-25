# ADR-0003: Defer Stripe to v1.1, ship v1.0 with manual billing

- **Date:** 2026-05-16
- **Status:** Accepted
- **Deciders:** Lead Architect

## Context

The original manifesto put Stripe integration in the MVP. With the v1.0 constraints clarified — solo dev, 6–8 weeks, ~50 target gyms — every week matters.

Stripe done properly is not trivial:
- Webhooks (idempotency, retries, signature verification)
- Subscription lifecycle (trial → active → past_due → canceled)
- Prorations (mid-cycle plan changes, freezes)
- Failed payment retry policy
- Tax (VAT/GST handling per jurisdiction)
- Refunds + disputes
- Test mode → live mode migration

A safe v1.0 Stripe implementation is 1.5–2 weeks of focused work, plus ongoing webhook debugging in production.

For the target customer profile (early-stage gyms, often RU/CIS leaning per geographic assumption), a large fraction settle payments via cash or local bank transfer outside any platform. They want the system to *record* that a payment happened, not necessarily *process* it.

## Decision

**v1.0 ships with manual billing only:**
- Admin marks a payment as received (cash / bank transfer / external card POS / other).
- System generates an invoice PDF and links it to the member's plan.
- Renewal reminders sent automatically before expiration.

**v1.1 adds Stripe:**
- Stripe Checkout for new subscriptions
- Webhook-driven subscription lifecycle
- Refunds + retries

The `payments` table is designed to accommodate both manual and Stripe sources from day one (a `source` enum column), so v1.1 is additive rather than a schema rewrite.

## Consequences

**Positive:**
- Saves 1.5–2 weeks on v1.0 timeline.
- v1.0 customers can be onboarded immediately without payment-processor setup.
- Manual billing remains a permanent feature (some gyms will always prefer it).

**Negative:**
- No online subscription self-serve at launch — members can't pay themselves.
- Manual data entry burden on staff.

**Mitigations:**
- Telegram bot can send a payment-due reminder with bank details / payment instructions configured per tenant.
- Bulk "mark paid" UX is a Sprint 3 task so staff isn't clicking one-by-one.

## Alternatives considered

- **Use a Stripe wrapper / hosted billing platform (Lago, Paddle).** Rejected: still requires integration, plus a vendor dependency, plus we lose ability to support cash/transfer cleanly.
- **Build Stripe minimally (just one-time payments, no subscriptions).** Rejected: even one-time payments need webhooks + idempotency, and we'd build the same infra twice when adding subscriptions later.
- **Ship without any payment tracking.** Rejected: knowing who's paid is core to gym operations.

## Notes

Manifesto updated to reflect this. ROADMAP places billing in Sprint 3 as manual; Stripe is in the backlog for v1.1.
