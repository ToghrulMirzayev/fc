"""Visits and Payments — operational events.

Visits record check-ins. One row per scan. Payments record received money,
manually marked by admin (Stripe deferred to v1.1).
"""

import enum
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin
from app.db.tenancy import TENANT_SCHEMA


class CheckinMethod(str, enum.Enum):
    QR = "qr"
    MANUAL = "manual"


class Visit(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "visits"
    __table_args__ = {"schema": TENANT_SCHEMA}

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    member_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{TENANT_SCHEMA}.members.id", ondelete="CASCADE"),
        index=True,
    )
    membership_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{TENANT_SCHEMA}.memberships.id", ondelete="RESTRICT")
    )
    method: Mapped[CheckinMethod] = mapped_column(
        Enum(CheckinMethod, values_callable=lambda x: [e.value for e in x])
    )
    # Who recorded it. Null for QR self-scans by member.
    recorded_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    checked_in_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PaymentSource(str, enum.Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CARD_EXTERNAL = "card_external"  # POS terminal, not us
    OTHER = "other"
    STRIPE = "stripe"  # reserved for v1.1


class Payment(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "payments"
    __table_args__ = {"schema": TENANT_SCHEMA}

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    member_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{TENANT_SCHEMA}.members.id", ondelete="CASCADE"),
        index=True,
    )
    membership_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(f"{TENANT_SCHEMA}.memberships.id", ondelete="SET NULL"),
        nullable=True,
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3))
    source: Mapped[PaymentSource] = mapped_column(
        Enum(PaymentSource, values_callable=lambda x: [e.value for e in x])
    )
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    recorded_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
