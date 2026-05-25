"""Add feature flags, signup requests, payment-locked memberships.

Revision ID: 0002_signup_and_flags
Revises: 0001_initial
Create Date: 2026-05-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_signup_and_flags"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


signup_status_enum = postgresql.ENUM(
    "pending", "contacted", "activated", "rejected",
    name="signuprequeststatus", create_type=False,
)
billing_tier_enum = postgresql.ENUM(
    "basic", "advanced", "pro", "premium", "corporate",
    name="billingplantier", create_type=False,
)


def upgrade() -> None:
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'signuprequeststatus') THEN
            CREATE TYPE signuprequeststatus AS ENUM ('pending', 'contacted', 'activated', 'rejected');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'billingplantier') THEN
            CREATE TYPE billingplantier AS ENUM ('basic', 'advanced', 'pro', 'premium', 'corporate');
        END IF;
    END$$;
    """)

    # Tenant: activation flag
    op.add_column(
        "tenants",
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.false()),
    )

    # Membership: payment lock
    op.add_column(
        "memberships",
        sa.Column("is_paid", sa.Boolean, nullable=False, server_default=sa.false()),
    )

    # Feature flags
    op.create_table(
        "feature_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("description", sa.String(500), nullable=True),
        sa.UniqueConstraint("tenant_id", "key", name="uq_feature_flag_tenant_key"),
    )
    op.create_index("ix_feature_flags_tenant_id", "feature_flags", ["tenant_id"])
    op.create_index("ix_feature_flags_key", "feature_flags", ["key"])

    op.create_table(
        "feature_flag_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("feature_flag_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("feature_flags.id", ondelete="CASCADE"), nullable=False),
        sa.Column("setting_key", sa.String(64), nullable=False),
        sa.Column("setting_value", sa.String(500), nullable=False),
        sa.UniqueConstraint("feature_flag_id", "setting_key", name="uq_flag_setting_key"),
    )
    op.create_index("ix_feature_flag_settings_feature_flag_id", "feature_flag_settings", ["feature_flag_id"])

    # Signup requests
    op.create_table(
        "signup_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(128), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("company_name", sa.String(128), nullable=False),
        sa.Column("country", sa.String(64), nullable=False),
        sa.Column("city", sa.String(64), nullable=True),
        sa.Column("estimated_members", sa.String(32), nullable=False),
        sa.Column("interested_tier", billing_tier_enum, nullable=False),
        sa.Column("notes", sa.String(2000), nullable=True),
        sa.Column("status", signup_status_enum, nullable=False, server_default="pending"),
    )
    op.create_index("ix_signup_requests_tenant_id", "signup_requests", ["tenant_id"])
    op.create_index("ix_signup_requests_email", "signup_requests", ["email"])


def downgrade() -> None:
    op.drop_table("signup_requests")
    op.drop_table("feature_flag_settings")
    op.drop_table("feature_flags")
    op.drop_column("memberships", "is_paid")
    op.drop_column("tenants", "is_active")
    op.execute("DROP TYPE IF EXISTS signuprequeststatus")
    op.execute("DROP TYPE IF EXISTS billingplantier")
