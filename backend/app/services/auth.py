"""Auth service: login, refresh, logout."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.models.audit import AuditLog, RefreshToken
from app.models.user import User


class AuthError(Exception):
    """Domain-level auth failure. Routers map to 401."""


async def login(db: AsyncSession, email: str, password: str) -> tuple[User, str, str]:
    """Verify credentials and issue access + refresh tokens.

    Returns (user, access_token, raw_refresh_token).
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Always do a dummy verify on no-user to keep timing constant.
    if user is None:
        # Argon2 verify takes ~50ms; do an equivalent computation here.
        verify_password(password, "$argon2id$v=19$m=65536,t=3,p=4$invalid$invalid")
        db.add(AuditLog(event="auth.login.failed", details=f"email={email}"))
        raise AuthError("invalid_credentials")

    if not user.is_active:
        db.add(
            AuditLog(
                event="auth.login.inactive",
                actor_user_id=user.id,
                tenant_id=user.tenant_id,
            )
        )
        raise AuthError("inactive")

    # Block staff login if their tenant hasn't been activated yet.
    # Super admins (no tenant) bypass this check.
    if user.tenant_id is not None:
        from app.models.tenant import Tenant
        tenant = await db.get(Tenant, user.tenant_id)
        if tenant is None or not tenant.is_active:
            db.add(
                AuditLog(
                    event="auth.login.tenant_locked",
                    actor_user_id=user.id,
                    tenant_id=user.tenant_id,
                )
            )
            raise AuthError("tenant_pending_activation")

    if not verify_password(password, user.password_hash):
        db.add(
            AuditLog(
                event="auth.login.failed",
                actor_user_id=user.id,
                tenant_id=user.tenant_id,
            )
        )
        raise AuthError("invalid_credentials")

    access = create_access_token(user.id, user.tenant_id, user.role.value)
    raw_refresh, refresh_hash = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS),
        )
    )
    db.add(
        AuditLog(
            event="auth.login.success",
            actor_user_id=user.id,
            tenant_id=user.tenant_id,
        )
    )
    return user, access, raw_refresh


async def refresh_tokens(
    db: AsyncSession, raw_refresh_token: str
) -> tuple[User, str, str]:
    """Rotate the refresh token: revoke old, issue new pair."""
    token_hash = hash_refresh_token(raw_refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    rt = result.scalar_one_or_none()
    if rt is None or rt.revoked_at is not None:
        raise AuthError("invalid_refresh")
    if rt.expires_at < datetime.now(UTC):
        raise AuthError("expired_refresh")

    user = await db.get(User, rt.user_id)
    if user is None or not user.is_active:
        raise AuthError("inactive")

    rt.revoked_at = datetime.now(UTC)

    access = create_access_token(user.id, user.tenant_id, user.role.value)
    raw_new, hash_new = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_new,
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS),
        )
    )
    return user, access, raw_new


async def revoke_all_user_tokens(db: AsyncSession, user_id: UUID) -> None:
    """Used on logout-everywhere or after password change."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
        )
    )
    now = datetime.now(UTC)
    for rt in result.scalars():
        rt.revoked_at = now
