"""Membership — a member's active or past subscription.

A member can have multiple historical memberships but only one ACTIVE or
FROZEN at a time (enforced by the service layer, not a DB constraint).

Fields are copied from MembershipPlan at creation time so plan changes
don't retroactively alter active memberships.
"""

import enum
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin
from app.models.plan import PlanType


class MembershipStatus(str, enum.Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    EXPIRED = "expired"
    CANCELED = "canceled"  # admin canceled (refund / mistake)


class Membership(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "memberships"

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    member_id: Mapped[UUID] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True
    )
    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("membership_plans.id", ondelete="RESTRICT")
    )

    # Snapshot from plan at creation
    plan_name: Mapped[str] = mapped_column(String(128))
    plan_type: Mapped[PlanType] = mapped_column(
        Enum(PlanType, values_callable=lambda x: [e.value for e in x])
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    starts_on: Mapped[date] = mapped_column(Date)
    expires_on: Mapped[date] = mapped_column(Date)

    # If the plan caps visits, this is the initial count.
    visit_limit: Mapped[int | None] = mapped_column(nullable=True)
    # Decremented on each check-in. None if unlimited.
    visits_remaining: Mapped[int | None] = mapped_column(nullable=True)

    max_freeze_days: Mapped[int] = mapped_column(default=30)
    max_freeze_count: Mapped[int] = mapped_column(default=2)
    # Sum of all freeze days used so far.
    freeze_days_used: Mapped[int] = mapped_column(default=0)
    freeze_count: Mapped[int] = mapped_column(default=0)

    status: Mapped[MembershipStatus] = mapped_column(
        Enum(MembershipStatus, values_callable=lambda x: [e.value for e in x]),
        default=MembershipStatus.ACTIVE,
    )
    # Card is locked until the member's plan is marked as paid.
    # Until then, check-ins are rejected and the member sees an
    # "awaiting payment" badge in the bot and admin profile.
    is_paid: Mapped[bool] = mapped_column(default=False)


class FreezePeriod(Base, UUIDPKMixin, TimestampMixin):
    """A period during which a membership was frozen.

    A membership can have multiple FreezePeriod records over its lifetime,
    one per freeze instance. `ends_on` is set at freeze start (planned
    auto-resume) and can be edited if the member resumes manually.
    """

    __tablename__ = "freeze_periods"

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    membership_id: Mapped[UUID] = mapped_column(
        ForeignKey("memberships.id", ondelete="CASCADE"), index=True
    )
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date] = mapped_column(Date)
    resumed_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
