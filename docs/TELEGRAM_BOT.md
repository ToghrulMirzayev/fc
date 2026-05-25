# Telegram Bot — setup and architecture notes

## How the bot runs

The bot is **not** a separate service. It's an aiogram 3.x dispatcher mounted inside the FastAPI app as a webhook endpoint at `POST /bot/webhook`. One process, one deployable.

Why webhook, not long-polling:
- No outbound polling overhead.
- Telegram → Caddy → FastAPI → aiogram is straightforward.
- Easier to reason about state (each update = one HTTP request).

## Local development

Telegram requires the webhook to be a public HTTPS URL. For local dev:

1. Get a bot token from `@BotFather`. Set `TELEGRAM_BOT_TOKEN` in `.env`.
2. Start a tunnel: `cloudflared tunnel --url http://localhost:8000` (or `ngrok http 8000`).
3. Set `TELEGRAM_WEBHOOK_URL` to `<tunnel-url>/bot/webhook` in `.env`.
4. Restart the API. On startup it calls `setWebhook` with the URL + secret.
5. Test: send `/start` to the bot.

## Account linking flow

```
1. Staff opens member profile in admin web → clicks "Generate linking code"
2. Backend creates a 6-digit code, stores in Redis with key
   `link:<code>` → {member_id, tenant_id, expires_at} (10 min TTL)
3. Staff shows code to the member (or it's printed on their welcome card)
4. Member sends the code to the bot in plain text
5. Bot validates the code, binds telegram_user_id → member record, deletes the Redis key
6. Bot replies with welcome + main menu
```

The Telegram user ID is stored on the `members` table as a nullable column.
A member can re-link (rotate their TG account) by repeating the flow; old binding is overwritten.

## QR command flow

```
1. Member taps "Show QR" in bot
2. Bot calls service: generate_qr_token(member_id, tenant_id)
3. Service signs payload with HMAC-SHA256 using QR_SIGNING_KEY,
   TTL = QR_TOKEN_TTL_SECONDS
4. QR image generated server-side (qrcode lib) and sent as photo
5. Caption includes auto-refresh hint
6. When scanner POSTs the token to /api/v1/checkins/scan,
   service verifies signature, checks Redis for nonce reuse,
   creates Visit record, returns member info to scanner
```

## Localization

Bot copy lives in `app/branding/__init__.py` under `BOT_COPY`. Each member has a `locale` field (defaults to their Telegram language code, falls back to "en"). The `bot_text()` helper picks the right string.

Adding a language = adding a key to `BOT_COPY` and translating all message keys.

## What the bot does NOT do in v1.0

- Direct payment processing (deferred with Stripe)
- Class booking management (Sprint 4 — possibly cut)
- Member-initiated freeze (admin-approved request only)
- Trainer interactions (no trainer-bot interaction yet)

## Security checklist

- [x] Webhook signed: aiogram validates `X-Telegram-Bot-Api-Secret-Token` header
- [x] Linking codes are single-use + 10 min TTL + 6 digits (1M space, brute-force-resistant with rate limit)
- [x] Rate limit on linking attempts: 5 per Telegram user ID per hour
- [x] QR tokens are HMAC-signed, single-use, short TTL
- [x] No PII in bot logs (only `telegram_user_id`, no names in error traces)
