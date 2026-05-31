"""Alembic environment.

Configured for async SQLAlchemy. Reads URL from app settings, autogenerate
metadata from app.models.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Make `app` importable when running alembic from the backend/ directory.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.tenancy import TENANT_SCHEMA  # noqa: E402
from app.models import *  # noqa: F401, F403, E402  — register all models

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url with the one from settings.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to) -> bool:
    """Keep the per-tenant (sentinel) schema out of autogenerate.

    Those tables are materialised per tenant by app.db.provision, not by
    Alembic, so Alembic must ignore the sentinel ``tenant`` schema.
    """
    if type_ == "table" and getattr(obj, "schema", None) == TENANT_SCHEMA:
        return False
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        # Commit after each migration so DDL like ALTER TYPE ... ADD VALUE
        # (0003 adds 'free' to billingplantier) is committed before a later
        # migration (0004) uses that new enum value — Postgres forbids using
        # a freshly added enum value in the same transaction.
        transaction_per_migration=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    cfg_section = config.get_section(config.config_ini_section, {})
    connectable = async_engine_from_config(
        cfg_section, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
