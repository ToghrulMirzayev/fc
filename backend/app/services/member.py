"""Member service.

All queries are scoped by tenant_id from the request context. The
calling router never passes tenant_id explicitly — it comes from the
current_user dependency.
"""

from datetime import date
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import require_current_tenant
from app.models.member import Member, MemberStatus
from app.models.membership import Membership, MembershipStatus
from app.models.plan import MembershipPlan
from app.models.tenant import Tenant
from app.schemas.member import (
    MemberCreate,
    MemberListItem,
    MemberUpdate,
    MembershipBrief,
)


def initials_of(name: str) -> str:
    """First letters of first and last word, uppercase."""
    parts = [p for p in name.strip().split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def days_left_to(d: date) -> int:
    return (d - date.today()).days


async def get_active_membership(
    db: AsyncSession, member_id: UUID
) -> Membership | None:
    """Return the active or frozen membership for a member, if any."""
    result = await db.execute(
        select(Membership)
        .where(
            Membership.member_id == member_id,
            Membership.status.in_(
                [MembershipStatus.ACTIVE, MembershipStatus.FROZEN]
            ),
        )
        .order_by(desc(Membership.created_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


def compute_member_status(
    membership: Membership | None,
) -> MemberStatus:
    """Pure function. Used both on the fly and in scheduled recomputes."""
    if membership is None:
        return MemberStatus.INACTIVE
    if membership.status == MembershipStatus.FROZEN:
        return MemberStatus.FROZEN
    if membership.expires_on < date.today():
        return MemberStatus.EXPIRED
    if membership.visit_limit is not None and (
        membership.visits_remaining or 0
    ) <= 0:
        return MemberStatus.EXPIRED
    return MemberStatus.ACTIVE


async def create_member(db: AsyncSession, payload: MemberCreate) -> Member:
    tenant_id = require_current_tenant()
    tenant = await db.get(Tenant, tenant_id)
    member = Member(
        tenant_id=tenant_id,
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        locale=payload.locale or (tenant.default_locale if tenant else "en"),
        status=MemberStatus.INACTIVE,
    )
    db.add(member)
    await db.flush()
    return member


async def update_member(
    db: AsyncSession, member: Member, payload: MemberUpdate
) -> Member:
    if payload.full_name is not None:
        member.full_name = payload.full_name
    if payload.phone is not None:
        member.phone = payload.phone
    if payload.email is not None:
        member.email = payload.email
    if payload.notes is not None:
        member.notes = payload.notes
    return member


async def list_members(
    db: AsyncSession,
    *,
    status_filter: str | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[MemberListItem], int, dict[str, int]]:
    """List members with optional filters. Returns (items, total, counts).

    counts is a histogram of statuses for filter chips, computed over the
    unfiltered set so the chips don't change when a filter is applied.
    """
    tenant_id = require_current_tenant()

    base = select(Member).where(Member.tenant_id == tenant_id)
    if search:
        like = f"%{search}%"
        base = base.where(
            (Member.full_name.ilike(like))
            | (Member.phone.ilike(like))
            | (Member.email.ilike(like))
        )

    # Counts (unfiltered by status)
    count_result = await db.execute(
        select(Member.status, func.count(Member.id))
        .where(Member.tenant_id == tenant_id)
        .group_by(Member.status)
    )
    counts = {row[0].value: row[1] for row in count_result.all()}
    counts["all"] = sum(counts.values())
    # Ensure all keys exist
    for s in ("active", "frozen", "expired", "inactive"):
        counts.setdefault(s, 0)

    if status_filter and status_filter != "all":
        base = base.where(Member.status == MemberStatus(status_filter))

    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar_one()

    result = await db.execute(
        base.order_by(Member.full_name).limit(limit).offset(offset)
    )
    members = result.scalars().all()

    items: list[MemberListItem] = []
    for m in members:
        active = await get_active_membership(db, m.id)
        items.append(
            MemberListItem(
                id=m.id,
                full_name=m.full_name,
                phone=m.phone,
                initials=initials_of(m.full_name),
                status=m.status.value,
                plan_name=active.plan_name if active else None,
                plan_type=active.plan_type.value if active else None,
                expires_on=active.expires_on if active else None,
                days_left=days_left_to(active.expires_on) if active else None,
                visits_remaining=active.visits_remaining if active else None,
                visit_limit=active.visit_limit if active else None,
            )
        )
    return items, total, counts


async def membership_to_brief(m: Membership) -> MembershipBrief:
    return MembershipBrief(
        id=m.id,
        plan_name=m.plan_name,
        plan_type=m.plan_type.value,
        starts_on=m.starts_on,
        expires_on=m.expires_on,
        visit_limit=m.visit_limit,
        visits_remaining=m.visits_remaining,
        status=m.status.value,
        days_left=days_left_to(m.expires_on),
        is_paid=m.is_paid,
    )


async def assign_plan(
    db: AsyncSession,
    member: Member,
    plan: MembershipPlan,
    starts_on: date | None = None,
) -> Membership:
    """Create a new active Membership from a plan.

    Existing active/frozen memberships for the member stay untouched — the
    service layer ensures we don't create overlapping active memberships
    via a check below.
    """
    from datetime import timedelta as _td

    existing = await get_active_membership(db, member.id)
    if existing is not None:
        raise ValueError("member_has_active_membership")

    starts = starts_on or date.today()
    membership = Membership(
        tenant_id=member.tenant_id,
        member_id=member.id,
        plan_id=plan.id,
        plan_name=plan.name,
        plan_type=plan.type,
        price=plan.price,
        starts_on=starts,
        expires_on=starts + _td(days=plan.duration_days),
        visit_limit=plan.visit_limit,
        visits_remaining=plan.visit_limit,
        max_freeze_days=plan.max_freeze_days,
        max_freeze_count=plan.max_freeze_count,
        status=MembershipStatus.ACTIVE,
    )
    db.add(membership)
    member.status = MemberStatus.ACTIVE
    await db.flush()
    return membership
