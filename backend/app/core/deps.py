"""FastAPI dependency providers.

- get_session — yields a DB session, commits on success, rolls back on error.
- get_current_user — decodes JWT, loads user, sets tenant context.
- require_role — RBAC guard.
"""

from collections.abc import Awaitable, Callable
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.core.tenant import set_current_tenant
from app.db.session import get_session
from app.models.user import User, UserRole

# Bearer auth scheme. auto_error=False because we want to return our own
# 401 shape rather than FastAPI's default.
_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_session),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    try:
        claims = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    if claims.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong token type",
        )

    try:
        user_id = UUID(claims["sub"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bad token subject",
        )

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Stash tenant_id in context for the rest of the request.
    set_current_tenant(user.tenant_id)
    return user


def require_role(
    *allowed: UserRole,
) -> Callable[[User], Awaitable[User]]:
    """Dependency factory that allows only specified roles.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role(UserRole.OWNER))])
    """

    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges",
            )
        return user

    return _check
