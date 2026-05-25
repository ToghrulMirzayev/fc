"""Telegram account linking codes.

Workflow:
1. Staff hits POST /api/v1/members/{id}/linking-code → returns 6-digit code
2. Code stored in Redis: link:<code> → {member_id, tenant_id} with 10 min TTL
3. Member sends code to the bot
4. Bot calls consume_linking_code, gets member, sets telegram_user_id, deletes Redis key
"""

import secrets
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis
from app.models.member import Member

LINKING_TTL_SECONDS = 600  # 10 minutes
LINKING_REDIS_PREFIX = "link:"


def _generate_code() -> str:
    # 6 digits with leading zeros possible. ~1M space; combined with
    # 10-minute TTL and rate-limiting on the bot side, brute force is
    # not practical.
    return f"{secrets.randbelow(1_000_000):06d}"


async def create_linking_code(member_id: UUID, tenant_id: UUID) -> str:
    code = _generate_code()
    key = f"{LINKING_REDIS_PREFIX}{code}"
    value = f"{member_id}|{tenant_id}"
    # NX so a collision doesn't overwrite an active code from someone else.
    # On the rare collision (1 in 1M), regenerate up to 5 times.
    for _ in range(5):
        ok = await redis.set(key, value, ex=LINKING_TTL_SECONDS, nx=True)
        if ok:
            return code
        code = _generate_code()
        key = f"{LINKING_REDIS_PREFIX}{code}"
        value = f"{member_id}|{tenant_id}"
    raise RuntimeError("Could not generate unique linking code after retries")


async def consume_linking_code(
    db: AsyncSession, code: str, telegram_user_id: int
) -> Member | None:
    """Returns the linked Member on success, None on bad/expired code."""
    key = f"{LINKING_REDIS_PREFIX}{code}"
    value = await redis.get(key)
    if value is None:
        return None
    try:
        member_id_s, _tenant_id_s = value.split("|")
        member_id = UUID(member_id_s)
    except (ValueError, AttributeError):
        return None

    member = await db.get(Member, member_id)
    if member is None:
        return None

    member.telegram_user_id = telegram_user_id
    await redis.delete(key)
    return member
