"""Schema-per-tenant helpers.

Multi-tenancy model: one Postgres database, two kinds of schema.

- The default ``public`` schema holds the *control plane* — tables that
  describe who exists and what they may do: tenants, users, refresh
  tokens, audit log, discounts, signup requests, feature flags. These are
  shared and queried directly.

- Each tenant's *data plane* lives in its own schema ``t_<slug>``:
  members, membership plans, memberships, freeze periods, visits and
  payments. These tables are declared on the ORM with the sentinel schema
  name :data:`TENANT_SCHEMA`. At runtime we translate that sentinel to the
  current tenant's real schema via SQLAlchemy's ``schema_translate_map``,
  so the exact same query only ever touches one tenant's schema.

Why this design:

- **Isolation.** A request scoped to tenant A can never read tenant B's
  members or payments — they are physically different tables in different
  schemas, and the connection is pinned to A's schema for the request.
- **Per-client backup.** ``pg_dump --schema=t_<slug>`` exports exactly one
  client's data and nothing else.

It all runs inside the single Postgres container of docker-compose; no
extra services are required.
"""

import re

# Sentinel schema declared on the tenant-scoped ORM models. This is never a
# real Postgres schema — it is always translated to a concrete ``t_<slug>``
# schema per request via ``schema_translate_map``.
TENANT_SCHEMA = "tenant"

# Slugs are validated on tenant creation, but we re-validate here because
# the value is interpolated into DDL / SET statements where it cannot be
# passed as a bind parameter.
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,48}$")


def schema_for_slug(slug: str) -> str:
    """Return the real Postgres schema name for a tenant slug.

    Hyphens become underscores so the schema name needs no quoting
    (``plan-free`` -> ``t_plan_free``).
    """
    if not slug or not _SLUG_RE.match(slug):
        raise ValueError(f"invalid tenant slug: {slug!r}")
    return "t_" + slug.replace("-", "_")


def translate_map(slug: str) -> dict[str | None, str]:
    """schema_translate_map mapping the sentinel to this tenant's schema."""
    return {TENANT_SCHEMA: schema_for_slug(slug)}
