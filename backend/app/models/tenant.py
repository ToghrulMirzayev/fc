"""Tenant — one gym = one tenant.

Every other tenant-scoped table has a `tenant_id` FK back here. The tenant
middleware (see app/core/tenant.py) resolves the current tenant from the
subdomain or X-Tenant-Slug header, and the base repository injects it into
every query.
"""

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin
from app.models.signup import BillingPlanTier


class Tenant(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "tenants"

    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    # Which pricing tier this gym is on. Drives feature/payment-method
    # availability. Concrete tier details live in app/core/billing_plans.py.
    billing_tier: Mapped[BillingPlanTier] = mapped_column(
        Enum(BillingPlanTier, values_callable=lambda x: [e.value for e in x]),
        default=BillingPlanTier.FREE,
        server_default=BillingPlanTier.FREE.value,
    )
    # Currency code (ISO 4217). Each gym configures its own.
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    # Default locale for the Telegram bot when a member's TG locale is unknown.
    default_locale: Mapped[str] = mapped_column(String(8), default="en")
    # QR token TTL — overridable per tenant. Default from settings.
    qr_ttl_seconds: Mapped[int] = mapped_column(default=30)
    # False until operator activates the tenant after reviewing signup.
    # When False, all staff users for this tenant are blocked from login.
    is_active: Mapped[bool] = mapped_column(default=False)
