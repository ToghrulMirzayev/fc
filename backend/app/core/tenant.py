"""Tenant context for the current request.

Set by `get_current_user` dependency from the JWT's `tid` claim. The
tenant context is then used by services to scope every query.

For v1.0 the tenant_id flows through the JWT only — we don't yet
parse subdomains because the frontend hits a single domain in dev. In
prod the frontend sends X-Tenant-Slug or uses subdomain; both paths
will resolve to the same tenant_id and be put on the request state.
"""

from contextvars import ContextVar
from uuid import UUID

_current_tenant_id: ContextVar[UUID | None] = ContextVar(
    "current_tenant_id", default=None
)


def set_current_tenant(tenant_id: UUID | None) -> None:
    _current_tenant_id.set(tenant_id)


def get_current_tenant() -> UUID | None:
    return _current_tenant_id.get()


def require_current_tenant() -> UUID:
    tid = _current_tenant_id.get()
    if tid is None:
        raise RuntimeError(
            "No tenant in context. This endpoint requires a tenant-scoped user."
        )
    return tid
