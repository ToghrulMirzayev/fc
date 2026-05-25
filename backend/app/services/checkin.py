"""Check-in service.

Two flows:
- QR scan: token from Telegram bot → /api/v1/checkins/scan
- Manual: receptionist clicks "Check in" on member → /api/v1/checkins/manual

Both flows funnel through `record_visit`, which handles:
- membership validation (active, not expired, has visits)
- anti-passback (cooldown)
- visit recording
- visits_remaining decrement
- audit log
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis
from app.core.security import verify_qr_token
from app.core.tenant import require_current_tenant
from app.models.audit import AuditLog
from app.models.member import Member
from app.models.membership import Membership, MembershipStatus
from app.models.visit import CheckinMethod, Visit

ANTI_PASSBACK_SECONDS = 60  # cooldown between consecutive check-ins
QR_NONCE_REDIS_PREFIX = "qr_used:"


class CheckinError(Exception):
    """Reason-coded check-in failure."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(detail or code)
        self.code = code


async def record_visit(
    db: AsyncSession,
    member: Member,
    method: CheckinMethod,
    recorded_by_user_id: UUID | None = None,
) -> tuple[Visit, Membership]:
    """Common check-in path. Validates and records the visit.

    Raises CheckinError with codes:
        - no_active_membership
        - membership_frozen
        - membership_expired
        - no_visits_left
        - anti_passback
    """
    # Find active or frozen membership
    result = await db.execute(
        select(Membership)
        .where(
            Membership.member_id == member.id,
            Membership.status.in_(
                [MembershipStatus.ACTIVE, MembershipStatus.FROZEN]
            ),
        )
        .order_by(desc(Membership.created_at))
        .limit(1)
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise CheckinError("no_active_membership")
    if not membership.is_paid:
        raise CheckinError("payment_pending")
    if membership.status == MembershipStatus.FROZEN:
        raise CheckinError("membership_frozen")
    if membership.expires_on < datetime.now(UTC).date():
        raise CheckinError("membership_expired")
    if (
        membership.visit_limit is not None
        and (membership.visits_remaining or 0) <= 0
    ):
        raise CheckinError("no_visits_left")

    # Anti-passback: reject if the same member checked in within cooldown
    cutoff = datetime.now(UTC) - timedelta(seconds=ANTI_PASSBACK_SECONDS)
    recent = await db.execute(
        select(Visit)
        .where(Visit.member_id == member.id, Visit.checked_in_at >= cutoff)
        .order_by(desc(Visit.checked_in_at))
        .limit(1)
    )
    if recent.scalar_one_or_none() is not None:
        raise CheckinError("anti_passback")

    visit = Visit(
        tenant_id=member.tenant_id,
        member_id=member.id,
        membership_id=membership.id,
        method=method,
        recorded_by_user_id=recorded_by_user_id,
    )
    db.add(visit)

    if membership.visits_remaining is not None:
        membership.visits_remaining -= 1

    db.add(
        AuditLog(
            tenant_id=member.tenant_id,
            actor_user_id=recorded_by_user_id,
            event="checkin.recorded",
            details=f"member={member.id} method={method.value}",
        )
    )
    await db.flush()
    return visit, membership


async def checkin_via_qr(
    db: AsyncSession, token: str
) -> tuple[Visit, Membership, Member]:
    """End-to-end QR check-in.

    1. Verify signature + expiry from the token itself.
    2. Burn the nonce in Redis (SET NX) to enforce single-use.
    3. Validate tenant matches the scanner's current tenant.
    4. Record the visit.
    """
    parsed = verify_qr_token(token)
    if parsed is None:
        raise CheckinError("invalid_qr")
    member_id, tenant_id, nonce = parsed

    current_tenant = require_current_tenant()
    if tenant_id != current_tenant:
        raise CheckinError("wrong_tenant")

    # Burn nonce. Redis SETNX with TTL = QR TTL upper bound (1 min is enough).
    nonce_key = f"{QR_NONCE_REDIS_PREFIX}{nonce}"
    was_set = await redis.set(nonce_key, "1", ex=120, nx=True)
    if not was_set:
        raise CheckinError("token_replay")

    member = await db.get(Member, member_id)
    if member is None or member.tenant_id != current_tenant:
        raise CheckinError("member_not_found")

    return (*(await record_visit(db, member, CheckinMethod.QR)), member)
