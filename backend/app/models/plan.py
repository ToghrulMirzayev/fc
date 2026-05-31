"""Membership plans — the catalog a gym offers.

A plan is a template. When a member signs up, we create a Membership
record from a Plan, copying the relevant fields so price/duration changes
to the plan don't retroactively affect active memberships.
"""

import enum
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin
from app.db.tenancy import TENANT_SCHEMA


class PlanType(str, enum.Enum):
    UNLIMITED_MONTHLY = "unlimited_monthly"
    LIMITED_VISITS = "limited_visits"  # e.g. 10 visits / month
    YEARLY = "yearly"
    ONE_TIME = "one_time"  # single-entry pass
    TRIAL = "trial"  # free trial


class MembershipPlan(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "membership_plans"
    __table_args__ = {"schema": TENANT_SCHEMA}

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(128))
    type: Mapped[PlanType] = mapped_column(
        Enum(PlanType, values_callable=lambda x: [e.value for e in x])
    )

    # Price in tenant's currency. Stored as Decimal to avoid float math.
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # Duration of the plan in days. For TRIAL and limited_visits this is the
    # window during which visits can be used.
    duration_days: Mapped[int] = mapped_column(default=30)

    # Visit cap. None = unlimited. Used by LIMITED_VISITS and TRIAL.
    visit_limit: Mapped[int | None] = mapped_column(nullable=True)

    # Freeze policy
    max_freeze_days: Mapped[int] = mapped_column(default=30)
    max_freeze_count: Mapped[int] = mapped_column(default=2)

    is_active: Mapped[bool] = mapped_column(default=True)
