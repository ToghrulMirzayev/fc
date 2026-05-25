"""Async Redis client.

Used for: QR nonce single-use tracking, account linking codes,
rate limiting (later), and Celery broker (separate DB).
"""

from redis.asyncio import Redis, from_url

from app.core.config import settings

redis: Redis = from_url(
    settings.REDIS_URL,
    decode_responses=True,
    encoding="utf-8",
)
