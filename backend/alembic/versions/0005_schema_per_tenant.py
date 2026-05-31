"""Schema-per-tenant: move client data out of public.

The tenant domain tables (members, membership_plans, memberships,
freeze_periods, visits, payments) no longer live in the shared ``public``
schema. Each tenant gets its own schema ``t_<slug>`` containing these
tables, provisioned by ``app.db.provision.provision_tenant_schema`` (run
by the seed script and, in the app, when a workspace is activated).

This migration drops the now-unused public copies. The Postgres ENUM types
they referenced are intentionally kept: the per-tenant tables reference the
same public enum types cross-schema, so we must not drop them.

Control-plane tables (tenants, users, refresh tokens, audit, discounts,
signup requests, feature flags) are unchanged and stay in public.

Revision ID: 0005_schema_per_tenant
Revises: 0004_billing_tier_and_discounts
"""

from typing import Union

from alembic import op

revision: str = "0005_schema_per_tenant"
down_revision: Union[str, None] = "0004_billing_tier_and_discounts"
branch_labels = None
depends_on = None

# Drop order respects FK dependencies (children first). CASCADE covers any
# remaining FKs defensively. Enum types are NOT dropped.
_TABLES = (
    "payments",
    "visits",
    "freeze_periods",
    "memberships",
    "members",
    "membership_plans",
)


def upgrade() -> None:
    for table in _TABLES:
        op.execute(f'DROP TABLE IF EXISTS public."{table}" CASCADE')


def downgrade() -> None:
    # Irreversible in practice: the data now lives in per-tenant schemas.
    # Recreating empty public tables would require the full original DDL;
    # we intentionally leave downgrade as a no-op rather than fabricate it.
    pass
