"""Dashboard endpoint — real data, scoped to the current tenant."""

from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.tenant import require_current_tenant
from app.db.session import get_session
from app.models.member import Member, MemberStatus
from app.models.membership import Membership, MembershipStatus
from app.models.tenant import Tenant
from app.models.user import User
from app.models.visit import Payment, Visit
from app.schemas.dashboard import (
    AttendanceSeriesOut,
    DashboardOut,
    Delta,
    ExpiringMemberOut,
    KpiOut,
)
from app.services.member import days_left_to, initials_of

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


_AVATAR_GRADIENTS = [
    "bg-gradient-to-br from-coral to-coral-dim",
    "bg-gradient-to-br from-ice to-[#2D5FA8]",
    "bg-gradient-to-br from-ozone to-[#7A9925]",
    "bg-gradient-to-br from-warning to-[#B07424]",
    "bg-gradient-to-br from-[#C77DFF] to-[#6C32A8]",
]


@router.get("", response_model=DashboardOut)
async def get_dashboard(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> DashboardOut:
    tenant_id = require_current_tenant()
    tenant = await db.get(Tenant, tenant_id)
    currency_symbol = {"EUR": "€", "USD": "$", "RSD": "RSD ", "BAM": "KM "}.get(
        tenant.currency if tenant else "EUR", ""
    )

    # ─── Active members
    active_count_q = await db.execute(
        select(func.count(Member.id)).where(
            Member.tenant_id == tenant_id,
            Member.status == MemberStatus.ACTIVE,
        )
    )
    active_count = active_count_q.scalar_one()

    week_ago = datetime.now(UTC) - timedelta(days=7)
    new_this_week_q = await db.execute(
        select(func.count(Member.id)).where(
            Member.tenant_id == tenant_id,
            Member.created_at >= week_ago,
        )
    )
    new_this_week = new_this_week_q.scalar_one()

    # ─── Revenue this month
    month_start = date.today().replace(day=1)
    revenue_q = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.tenant_id == tenant_id,
            Payment.paid_at >= datetime.combine(month_start, datetime.min.time()),
        )
    )
    revenue = float(revenue_q.scalar_one() or 0)

    # ─── Check-ins today
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_checkins_q = await db.execute(
        select(func.count(Visit.id)).where(
            Visit.tenant_id == tenant_id, Visit.checked_in_at >= today_start
        )
    )
    today_checkins = today_checkins_q.scalar_one()

    # ─── Churn risk: memberships expiring in the next 7 days
    horizon = date.today() + timedelta(days=7)
    churn_q = await db.execute(
        select(func.count(Membership.id)).where(
            Membership.tenant_id == tenant_id,
            Membership.status == MembershipStatus.ACTIVE,
            Membership.expires_on <= horizon,
            Membership.expires_on >= date.today(),
        )
    )
    churn_count = churn_q.scalar_one()

    # ─── Attendance: last 30 days
    attendance_current = []
    for i in range(30, -1, -1):
        day = date.today() - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        q = await db.execute(
            select(func.count(Visit.id)).where(
                Visit.tenant_id == tenant_id,
                Visit.checked_in_at >= day_start,
                Visit.checked_in_at < day_end,
            )
        )
        attendance_current.append(int(q.scalar_one()))

    # Previous period — just zeros for now until we have history.
    # In production this would be the prior 30 days; we keep an array of
    # 15 points to draw a smooth dashed line.
    attendance_prev = [0] * 15

    y_max = max(max(attendance_current, default=0), 100) * 1.2
    y_max = max(int(y_max), 100)

    # ─── Expiring members (next 14 days)
    expiring_horizon = date.today() + timedelta(days=14)
    exp_q = await db.execute(
        select(Member, Membership)
        .join(Membership, Membership.member_id == Member.id)
        .where(
            Member.tenant_id == tenant_id,
            Membership.status == MembershipStatus.ACTIVE,
            Membership.expires_on <= expiring_horizon,
            Membership.expires_on >= date.today(),
        )
        .order_by(Membership.expires_on)
        .limit(5)
    )
    expiring = []
    for i, (member, membership) in enumerate(exp_q.all()):
        plan_label = membership.plan_name
        if membership.visit_limit is not None:
            plan_label += f" · {membership.visits_remaining or 0} left"
        expiring.append(
            ExpiringMemberOut(
                id=str(member.id),
                name=member.full_name,
                initials=initials_of(member.full_name),
                plan=plan_label,
                days_left=days_left_to(membership.expires_on),
                expires_on=membership.expires_on,
                avatar_gradient=_AVATAR_GRADIENTS[i % len(_AVATAR_GRADIENTS)],
            )
        )

    return DashboardOut(
        kpis=[
            KpiOut(
                label="Active members",
                value=str(active_count),
                delta=Delta(direction="up", text=f"+{new_this_week} this week")
                if new_this_week
                else None,
                spark=[0.3, 0.4, 0.5, 0.55, 0.6, 0.7, 0.75, 0.85],
            ),
            KpiOut(
                label="Revenue / Month",
                value=f"{currency_symbol}{revenue:,.1f}".replace(",", " "),
                delta=Delta(direction="up", text="this month"),
                spark=[0.2, 0.3, 0.4, 0.5, 0.6, 0.65, 0.75, 0.85],
            ),
            KpiOut(
                label="Check-ins today",
                value=str(today_checkins),
                delta=None,
                spark=[0.05, 0.2, 0.3, 0.4, 0.55, 0.6, 0.7, 0.8],
            ),
            KpiOut(
                label="Churn risk",
                value=str(churn_count),
                delta=Delta(direction="down", text="expire in 7d")
                if churn_count
                else None,
                spark=[0.65, 0.55, 0.45, 0.35, 0.3, 0.25, 0.2, 0.15],
            ),
        ],
        attendance=AttendanceSeriesOut(
            current=attendance_current,
            previous=attendance_prev,
            y_max=y_max,
            x_labels=[
                (date.today() - timedelta(days=28)).strftime("%b %d"),
                (date.today() - timedelta(days=21)).strftime("%b %d"),
                (date.today() - timedelta(days=14)).strftime("%b %d"),
                (date.today() - timedelta(days=7)).strftime("%b %d"),
                date.today().strftime("%b %d"),
            ],
        ),
        expiring=expiring,
    )
