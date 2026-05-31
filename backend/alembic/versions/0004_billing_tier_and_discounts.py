"""Add tenants.billing_tier and the discounts table.

Revision ID: 0004_billing_tier_and_discounts
Revises: 0003_free_tier
Create Date: 2026-05-31
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_billing_tier_and_discounts"
down_revision: Union[str, None] = "0003_free_tier"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Reuse the existing enum type (created in 0002, 'free' added in 0003).
billing_tier_enum = postgresql.ENUM(
    "free", "basic", "advanced", "pro", "premium", "corporate",
    name="billingplantier", create_type=False,
)


def upgrade() -> None:
    # Tenant: which pricing tier the gym is on.
    op.add_column(
        "tenants",
        sa.Column(
            "billing_tier",
            billing_tier_enum,
            nullable=False,
            server_default="free",
        ),
    )

    # Discounts: operator-configurable promo percentages, keyed by scope.
    op.create_table(
        "discounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("scope", sa.String(64), nullable=False),
        sa.Column("percent", sa.Integer, nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("label", sa.String(200), nullable=True),
        sa.UniqueConstraint("scope", name="uq_discount_scope"),
    )
    op.create_index("ix_discounts_scope", "discounts", ["scope"])


def downgrade() -> None:
    op.drop_index("ix_discounts_scope", table_name="discounts")
    op.drop_table("discounts")
    op.drop_column("tenants", "billing_tier")
