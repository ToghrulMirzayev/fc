"""Add free tier to billingplantier enum.

Revision ID: 0003_free_tier
Revises: 0002_signup_and_flags
Create Date: 2026-05-19
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0003_free_tier"
down_revision: Union[str, None] = "0002_signup_and_flags"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new value before 'basic' for natural ordering. Postgres requires
    # this DDL to run outside a transaction in some versions; Alembic handles
    # it for us in modern installs.
    op.execute("ALTER TYPE billingplantier ADD VALUE IF NOT EXISTS 'free' BEFORE 'basic'")


def downgrade() -> None:
    # Removing an enum value is not natively supported in Postgres without
    # rewriting the type. Leaving as a no-op; the value can be ignored.
    pass
