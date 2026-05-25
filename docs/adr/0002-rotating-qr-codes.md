# ADR-0002: Rotating QR codes for member check-in

- **Date:** 2026-05-16
- **Status:** Accepted
- **Deciders:** Lead Architect

## Context

Members check in to the gym by presenting a QR code (displayed in the Telegram bot) at the front desk. The original manifesto specified "QR code" but did not address the security model.

A naive implementation — one static QR per member — is insecure: a single screenshot equals unlimited free entries shared between people forever.

## Decision

QR codes are **rotating, short-lived, single-use tokens**:

- Token format: HMAC-SHA256-signed payload containing `member_id`, `tenant_id`, `issued_at`, `nonce`.
- TTL: 30 seconds (configurable per tenant via `QR_TOKEN_TTL_SECONDS`).
- Single-use: scanner endpoint records the token nonce in Redis with TTL = QR TTL. Second scan of the same nonce within the TTL window is rejected.
- Signing key: separate from app `SECRET_KEY` (`QR_SIGNING_KEY` env). Allows rotation without invalidating sessions.
- Bot refreshes the QR on demand. Frontend can also refresh on a timer if displayed in a web context later.

The scanner is a page in the admin web that uses the device camera (HTML5 QR scanner library) and POSTs the decoded token to `/api/v1/checkins/scan`.

## Consequences

**Positive:**
- Eliminates the screenshot-sharing attack.
- No PII in the QR — even if intercepted, the token reveals only opaque IDs.
- Signing key rotation is cheap.

**Negative:**
- Slightly worse UX: members must open the bot and tap "Show QR" each time. The QR can't be saved as a wallet pass in v1.0.
- Requires Redis for the nonce store (already in stack).
- If clocks drift between bot client and server by > TTL, scans fail. Mitigation: server uses `issued_at` from the signed payload, not client time.

## Alternatives considered

- **Static per-member QR** — rejected, see above.
- **HOTP / counter-based tokens** — rejected as more complex than time-based; TOTP-style (which this effectively is) is enough.
- **NFC instead of QR** — rejected: requires reader hardware at the gym front desk. QR works with a phone or USB scanner.
- **Bluetooth proximity** — rejected as overkill and battery-intensive.

## Notes

This wasn't in the original manifesto and is now mandatory. Added to manifesto change log.
