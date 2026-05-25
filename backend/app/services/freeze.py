"""Freeze service — pause and resume memberships."""

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.membership import FreezePeriod, Membership, MembershipStatus


class FreezeError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


async def freeze_membership(
    db: AsyncSession,
    membership: Membership,
    ends_on: date,
    actor_user_id: UUID | None = None,
    reason: str | None = None,
) -> FreezePeriod:
    if membership.status != MembershipStatus.ACTIVE:
        raise FreezeError("not_active")
    today = date.today()
    if ends_on <= today:
        raise FreezeError("ends_on_must_be_future")

    requested_days = (ends_on - today).days
    if (
        membership.freeze_days_used + requested_days
        > membership.max_freeze_days
    ):
        raise FreezeError("exceeds_max_freeze_days")
    if membership.freeze_count + 1 > membership.max_freeze_count:
        raise FreezeError("exceeds_max_freeze_count")

    period = FreezePeriod(
        tenant_id=membership.tenant_id,
        membership_id=membership.id,
        starts_on=today,
        ends_on=ends_on,
        reason=reason,
    )
    db.add(period)
    membership.status = MembershipStatus.FROZEN
    membership.freeze_count += 1
    # Extend expiration by the freeze duration so paid time isn't lost.
    delta_days = (ends_on - today).days
    membership.expires_on = membership.expires_on.fromordinal(
        membership.expires_on.toordinal() + delta_days
    )

    db.add(
        AuditLog(
            tenant_id=membership.tenant_id,
            actor_user_id=actor_user_id,
            event="membership.freeze",
            details=f"membership={membership.id} until={ends_on.isoformat()}",
        )
    )
    return period


async def resume_membership(
    db: AsyncSession,
    membership: Membership,
    actor_user_id: UUID | None = None,
) -> None:
    if membership.status != MembershipStatus.FROZEN:
        raise FreezeError("not_frozen")

    today = date.today()
    # Find the open freeze period
    result = await db.execute(
        select(FreezePeriod)
        .where(
            FreezePeriod.membership_id == membership.id,
            FreezePeriod.resumed_on.is_(None),
        )
        .order_by(FreezePeriod.starts_on.desc())
        .limit(1)
    )
    period = result.scalar_one_or_none()
    if period is None:
        # Defensive: status says frozen but no open period. Just resume.
        membership.status = MembershipStatus.ACTIVE
        return

    period.resumed_on = today
    used_days = (today - period.starts_on).days
    membership.freeze_days_used += used_days

    # If member resumed early, give back the unused freeze days from
    # the expiration extension.
    planned_days = (period.ends_on - period.starts_on).days
    if used_days < planned_days:
        diff = planned_days - used_days
        membership.expires_on = membership.expires_on.fromordinal(
            membership.expires_on.toordinal() - diff
        )

    membership.status = MembershipStatus.ACTIVE
    db.add(
        AuditLog(
            tenant_id=membership.tenant_id,
            actor_user_id=actor_user_id,
            event="membership.resume",
            details=f"membership={membership.id} used_days={used_days}",
        )
    )
