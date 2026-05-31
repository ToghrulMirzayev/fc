"""Discounts — operator-configurable promo percentages, by scope.

A discount is keyed by a stable `scope` string (e.g. "payments",
"access_control", ...). Application code looks a discount up by scope and,
if it's active, applies `percent` off the relevant upgrade price.

This is deliberately generic so we can add a discount for a new area
later by inserting a row — no schema change, no code change beyond
reading the new scope where it's needed.

Global by design: one row per scope, applies to all tenants. (If we ever
need per-tenant overrides we'd add a nullable tenant_id and prefer the
tenant-specific row over the global one.)
"""

from sqlalchemy import Boolean, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class Discount(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "discounts"
    __table_args__ = (
        UniqueConstraint("scope", name="uq_discount_scope"),
    )

    # Stable area key the discount applies to, e.g. "payments".
    scope: Mapped[str] = mapped_column(String(64), index=True)
    # Whole-number percent off, 0–100.
    percent: Mapped[int] = mapped_column(Integer, default=0)
    # When False the discount is ignored (kept for history / quick toggle).
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Short marketing label shown in the upgrade popup, e.g.
    # "Launch offer — 20% off".
    label: Mapped[str | None] = mapped_column(String(200), nullable=True)
