"""Async SQLAlchemy engine + session factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.db.tenancy import translate_map

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency. Yields a session, commits on success, rolls back on error."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def apply_tenant_schema(session: AsyncSession, slug: str) -> None:
    """Pin this session's connection to the tenant's schema.

    After this call, every tenant-scoped model (those declared with the
    ``tenant`` sentinel schema) resolves to ``t_<slug>`` for the life of
    the connection — i.e. the rest of the request. Control-plane tables
    (public) are unaffected.

    NOTE: we mutate the execution options on the *existing* connection in
    place rather than passing ``execution_options`` to ``session.connection``.
    Once a connection has already been procured for the session (e.g. an
    earlier ``db.get(User)`` in ``get_current_user``), SQLAlchemy ignores
    execution options passed to ``Session.connection(...)``, which would
    leave the sentinel ``tenant`` schema untranslated. ``schema_translate_map``
    is read at statement-execution time, so setting it now applies to every
    subsequent query on this connection.
    """
    tmap = translate_map(slug)
    conn = await session.connection()
    await conn.run_sync(
        lambda sync_conn: sync_conn.execution_options(schema_translate_map=tmap)
    )


@asynccontextmanager
async def tenant_session(slug: str) -> AsyncGenerator[AsyncSession, None]:
    """Open a session already pinned to one tenant's schema.

    For code paths that are not behind ``get_current_user`` (seed scripts,
    background jobs). Commits on success, rolls back on error.
    """
    async with SessionLocal() as session:
        await apply_tenant_schema(session, slug)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
