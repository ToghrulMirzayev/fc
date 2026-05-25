"""Signup requests from prospective gym clients.

Public form on the landing page creates a SignupRequest + an associated
Tenant (provisioned but locked). The operator (Keybit team) reviews and
activates from a super-admin panel later.

The tenant is created immediately so the prospective client gets their
subdomain reserved. They cannot log in until we activate them.
"""

import enum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class SignupRequestStatus(str, enum.Enum):
    PENDING = "pending"
    CONTACTED = "contacted"
    ACTIVATED = "activated"
    REJECTED = "rejected"


class BillingPlanTier(str, enum.Enum):
    """Our pricing tiers offered to gym operators (clients).

    Distinct from MembershipPlan (which is what gyms sell to their members).
    Concrete prices live in app/core/billing_plans.py constants, not the DB.
    """

    FREE = "free"
    BASIC = "basic"
    ADVANCED = "advanced"
    PRO = "pro"
    PREMIUM = "premium"
    CORPORATE = "corporate"


class SignupRequest(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "signup_requests"

    # Provisioned tenant linked at request time. Tenant exists but is
    # locked until activation.
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )

    # Contact info
    full_name: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[str] = mapped_column(String(32))
    company_name: Mapped[str] = mapped_column(String(128))

    # Survey answers
    country: Mapped[str] = mapped_column(String(64))
    city: Mapped[str | None] = mapped_column(String(64), nullable=True)
    estimated_members: Mapped[str] = mapped_column(String(32))  # range, e.g. "100-300"
    interested_tier: Mapped[BillingPlanTier] = mapped_column(
        Enum(BillingPlanTier, values_callable=lambda x: [e.value for e in x])
    )
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    status: Mapped[SignupRequestStatus] = mapped_column(
        Enum(SignupRequestStatus, values_callable=lambda x: [e.value for e in x]),
        default=SignupRequestStatus.PENDING,
    )
