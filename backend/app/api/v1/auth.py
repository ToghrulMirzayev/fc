"""Auth endpoints."""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.features import resolve_features
from app.db.session import get_session
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import (
    CurrentUserOut,
    LoginIn,
    RefreshIn,
    TokenPair,
    UpdateMeIn,
)
from app.core.config import settings
from app.services.auth import AuthError, login, refresh_tokens

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
async def login_endpoint(
    response: Response,
    payload: LoginIn,
    db: AsyncSession = Depends(get_session),
) -> TokenPair:
    try:
        _user, access, refresh = await login(
            db,
            payload.email,
            payload.password,
            tenant_slug=payload.workspace_slug,
        )
    except AuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=settings.ENV != "dev",
        samesite="lax",
        path="/api/v1/auth",
        max_age=settings.REFRESH_TOKEN_TTL_DAYS * 24 * 60 * 60,
    )
    return TokenPair(access_token=access)


@router.post("/refresh", response_model=TokenPair)
async def refresh_endpoint(
    response: Response,
    payload: RefreshIn | None = None,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_session),
) -> TokenPair:
    token = refresh_token or (payload.refresh_token if payload else None)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )
    try:
        _user, access, new_refresh = await refresh_tokens(db, token)
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=settings.ENV != "dev",
        samesite="lax",
        path="/api/v1/auth",
        max_age=settings.REFRESH_TOKEN_TTL_DAYS * 24 * 60 * 60,
    )
    return TokenPair(access_token=access)


@router.post("/logout")
async def logout_endpoint(
    response: Response,
) -> dict[str, str]:
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
        secure=settings.ENV != "dev",
        samesite="lax",
        httponly=True,
    )
    return {"status": "ok"}


async def _current_user_out(db: AsyncSession, user: User) -> CurrentUserOut:
    tenant = await db.get(Tenant, user.tenant_id) if user.tenant_id else None
    features = await resolve_features(db, user.tenant_id)
    return CurrentUserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        tenant_id=user.tenant_id,
        tenant_slug=tenant.slug if tenant else None,
        tenant_name=tenant.name if tenant else None,
        features=features,
    )


@router.get("/me", response_model=CurrentUserOut)
async def me_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> CurrentUserOut:
    return await _current_user_out(db, user)


@router.patch("/me", response_model=CurrentUserOut)
async def update_me_endpoint(
    payload: UpdateMeIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> CurrentUserOut:
    """Update the signed-in user's own personal data (name, email).

    Email must stay globally unique. Only the fields present in the
    request body are touched.
    """
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()

    if payload.email is not None and payload.email != user.email:
        existing = await db.execute(
            select(User).where(User.email == payload.email, User.id != user.id)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail="email_already_in_use")
        user.email = payload.email

    await db.commit()
    await db.refresh(user)
    return await _current_user_out(db, user)
