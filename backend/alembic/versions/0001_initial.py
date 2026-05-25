"""Initial schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-17

ENUM handling: we use postgresql.ENUM(..., create_type=False) which
SQLAlchemy treats as a pure reference — it never emits CREATE TYPE.
The types are created once at the top of upgrade() via raw SQL.

Why not sa.Enum? Because sa.Enum with create_type=False still triggers
auto-create in some SQLAlchemy versions during create_table. The
postgresql.ENUM dialect variant respects create_type=False reliably.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Reusable ENUM references — never emit DDL on their own.
user_role_enum = postgresql.ENUM(
    "super_admin", "owner", "manager", "receptionist", "trainer",
    name="userrole", create_type=False,
)
plan_type_enum = postgresql.ENUM(
    "unlimited_monthly", "limited_visits", "yearly", "one_time", "trial",
    name="plantype", create_type=False,
)
member_status_enum = postgresql.ENUM(
    "active", "frozen", "expired", "inactive",
    name="memberstatus", create_type=False,
)
membership_status_enum = postgresql.ENUM(
    "active", "frozen", "expired", "canceled",
    name="membershipstatus", create_type=False,
)
checkin_method_enum = postgresql.ENUM(
    "qr", "manual",
    name="checkinmethod", create_type=False,
)
payment_source_enum = postgresql.ENUM(
    "cash", "bank_transfer", "card_external", "other", "stripe",
    name="paymentsource", create_type=False,
)


def upgrade() -> None:
    # Create all PG ENUM types via raw SQL, idempotently. The DO block
    # protects against partial-state volumes where some enums already exist.
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
            CREATE TYPE userrole AS ENUM ('super_admin', 'owner', 'manager', 'receptionist', 'trainer');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'plantype') THEN
            CREATE TYPE plantype AS ENUM ('unlimited_monthly', 'limited_visits', 'yearly', 'one_time', 'trial');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'memberstatus') THEN
            CREATE TYPE memberstatus AS ENUM ('active', 'frozen', 'expired', 'inactive');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'membershipstatus') THEN
            CREATE TYPE membershipstatus AS ENUM ('active', 'frozen', 'expired', 'canceled');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'checkinmethod') THEN
            CREATE TYPE checkinmethod AS ENUM ('qr', 'manual');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'paymentsource') THEN
            CREATE TYPE paymentsource AS ENUM ('cash', 'bank_transfer', 'card_external', 'other', 'stripe');
        END IF;
    END$$;
    """)

    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("default_locale", sa.String(8), nullable=False, server_default="en"),
        sa.Column("qr_ttl_seconds", sa.Integer, nullable=False, server_default="30"),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"])

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(128), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "membership_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("type", plan_type_enum, nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("duration_days", sa.Integer, nullable=False, server_default="30"),
        sa.Column("visit_limit", sa.Integer, nullable=True),
        sa.Column("max_freeze_days", sa.Integer, nullable=False, server_default="30"),
        sa.Column("max_freeze_count", sa.Integer, nullable=False, server_default="2"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_membership_plans_tenant_id", "membership_plans", ["tenant_id"])

    op.create_table(
        "members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(128), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("telegram_user_id", sa.BigInteger, nullable=True, unique=True),
        sa.Column("locale", sa.String(8), nullable=False, server_default="en"),
        sa.Column("status", member_status_enum, nullable=False, server_default="inactive"),
        sa.Column("notes", sa.String(2000), nullable=True),
        sa.UniqueConstraint("tenant_id", "phone", name="uq_member_tenant_phone"),
    )
    op.create_index("ix_members_tenant_id", "members", ["tenant_id"])
    op.create_index("ix_members_telegram_user_id", "members", ["telegram_user_id"])

    op.create_table(
        "memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("membership_plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("plan_name", sa.String(128), nullable=False),
        sa.Column("plan_type", plan_type_enum, nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("starts_on", sa.Date, nullable=False),
        sa.Column("expires_on", sa.Date, nullable=False),
        sa.Column("visit_limit", sa.Integer, nullable=True),
        sa.Column("visits_remaining", sa.Integer, nullable=True),
        sa.Column("max_freeze_days", sa.Integer, nullable=False, server_default="30"),
        sa.Column("max_freeze_count", sa.Integer, nullable=False, server_default="2"),
        sa.Column("freeze_days_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("freeze_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", membership_status_enum, nullable=False, server_default="active"),
    )
    op.create_index("ix_memberships_tenant_id", "memberships", ["tenant_id"])
    op.create_index("ix_memberships_member_id", "memberships", ["member_id"])

    op.create_table(
        "freeze_periods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("membership_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("memberships.id", ondelete="CASCADE"), nullable=False),
        sa.Column("starts_on", sa.Date, nullable=False),
        sa.Column("ends_on", sa.Date, nullable=False),
        sa.Column("resumed_on", sa.Date, nullable=True),
        sa.Column("reason", sa.String(500), nullable=True),
    )
    op.create_index("ix_freeze_periods_membership_id", "freeze_periods", ["membership_id"])

    op.create_table(
        "visits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=False),
        sa.Column("membership_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("memberships.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("method", checkin_method_enum, nullable=False),
        sa.Column("recorded_by_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_visits_tenant_id", "visits", ["tenant_id"])
    op.create_index("ix_visits_member_id", "visits", ["member_id"])

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=False),
        sa.Column("membership_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("source", payment_source_enum, nullable=False),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("recorded_by_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_payments_tenant_id", "payments", ["tenant_id"])
    op.create_index("ix_payments_member_id", "payments", ["member_id"])

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event", sa.String(64), nullable=False),
        sa.Column("details", sa.String(2000), nullable=True),
    )
    op.create_index("ix_audit_log_tenant_id", "audit_log", ["tenant_id"])
    op.create_index("ix_audit_log_event", "audit_log", ["event"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("audit_log")
    op.drop_table("payments")
    op.drop_table("visits")
    op.drop_table("freeze_periods")
    op.drop_table("memberships")
    op.drop_table("members")
    op.drop_table("membership_plans")
    op.drop_table("users")
    op.drop_table("tenants")
    for enum_name in [
        "paymentsource", "checkinmethod", "membershipstatus",
        "memberstatus", "plantype", "userrole",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
