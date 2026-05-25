"""Feature flags.

Two-table design:
- feature_flags: key + enabled bool. The on/off switch.
- feature_flag_settings: key + setting_name + value. Per-flag config.

Example: `signup_discount` flag with settings:
  - percent: "15"
  - message: "First-month discount available"

Settings are stored as strings; consumers parse them. Keeps the schema
generic instead of growing a column per flag.

Scoping: a flag with `tenant_id` is per-tenant; a flag with NULL
`tenant_id` is global (operator-controlled, applies to landing page
and all tenants by default).
"""

from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class FeatureFlag(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "feature_flags"
    __table_args__ = (
        UniqueConstraint("tenant_id", "key", name="uq_feature_flag_tenant_key"),
    )

    # Null = global flag (operator-level).
    tenant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True
    )
    key: Mapped[str] = mapped_column(String(64), index=True)
    enabled: Mapped[bool] = mapped_column(default=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)


class FeatureFlagSetting(Base, UUIDPKMixin, TimestampMixin):
    """A single setting attached to a flag. Multiple per flag."""

    __tablename__ = "feature_flag_settings"
    __table_args__ = (
        UniqueConstraint(
            "feature_flag_id", "setting_key", name="uq_flag_setting_key"
        ),
    )

    feature_flag_id: Mapped[UUID] = mapped_column(
        ForeignKey("feature_flags.id", ondelete="CASCADE"), index=True
    )
    setting_key: Mapped[str] = mapped_column(String(64))
    setting_value: Mapped[str] = mapped_column(String(500))
