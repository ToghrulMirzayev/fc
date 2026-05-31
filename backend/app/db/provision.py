"""Create / drop per-tenant schemas.

A tenant's domain tables (members, plans, memberships, freeze periods,
visits, payments) are declared on the ORM with the sentinel ``tenant``
schema. To physically materialise them for a tenant we:

1. ``CREATE SCHEMA t_<slug>``
2. create those tables inside it, translating the sentinel schema to the
   real one.

Enum types stay in ``public`` (created once by the initial migration) and
are referenced cross-schema, so we never duplicate them per tenant.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.base import Base
from app.db.tenancy import TENANT_SCHEMA, schema_for_slug


def tenant_tables() -> list:
    """Table objects that live in the per-tenant (sentinel) schema."""
    return [t for t in Base.metadata.sorted_tables if t.schema == TENANT_SCHEMA]


async def provision_tenant_schema(conn: AsyncConnection, slug: str) -> str:
    """Create schema ``t_<slug>`` and its tables. Returns the schema name.

    Idempotent: safe to call again for an existing tenant.
    """
    schema = schema_for_slug(slug)
    await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
    tables = tenant_tables()

    def _create(sync_conn) -> None:
        bound = sync_conn.execution_options(
            schema_translate_map={TENANT_SCHEMA: schema}
        )
        Base.metadata.create_all(bound, tables=tables, checkfirst=True)

    await conn.run_sync(_create)
    return schema


async def drop_tenant_schema(conn: AsyncConnection, slug: str) -> None:
    """Drop a tenant's schema and everything in it. Used on de-provisioning
    or to reset a tenant before re-seeding."""
    schema = schema_for_slug(slug)
    await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
