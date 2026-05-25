"""Public endpoints — no auth required.

These power the marketing site / landing page:
- POST /api/v1/public/signup — submit a signup request
- GET  /api/v1/public/billing-plans — pricing tiers
- GET  /api/v1/public/discount — current discount flag state
"""

from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.billing_plans import BILLING_PLANS
from app.core.config import settings
from app.db.session import get_session
from app.services.feature_flag import get_flag
from app.services.signup import SignupError, submit_signup

router = APIRouter(prefix="/public", tags=["public"])


class SignupIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=128)
    email: EmailStr
    phone: str = Field(min_length=4, max_length=32)
    company_name: str = Field(min_length=2, max_length=128)
    country: str = Field(min_length=2, max_length=64)
    city: str | None = Field(default=None, max_length=64)
    estimated_members: str = Field(min_length=1, max_length=32)
    interested_tier: str  # BillingPlanTier value
    notes: str | None = Field(default=None, max_length=2000)


class SignupOut(BaseModel):
    request_id: str
    tenant_slug: str
    tenant_url: str
    welcome_message: str
    discount_active: bool


@router.post("/signup", response_model=SignupOut)
async def signup_endpoint(
    payload: SignupIn,
    db: AsyncSession = Depends(get_session),
) -> SignupOut:
    try:
        result = await submit_signup(
            db,
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
            company_name=payload.company_name,
            country=payload.country,
            city=payload.city,
            estimated_members=payload.estimated_members,
            interested_tier=payload.interested_tier,
            notes=payload.notes,
            app_domain=settings.APP_DOMAIN,
        )
    except SignupError as e:
        raise HTTPException(status_code=400, detail=e.code)
    return SignupOut(
        request_id=result.request_id,
        tenant_slug=result.tenant_slug,
        tenant_url=result.tenant_url,
        welcome_message=result.welcome_message,
        discount_active=result.discount_active,
    )


@router.get("/billing-plans")
async def billing_plans_endpoint() -> dict:
    return {
        "plans": [
            {
                "tier": p.tier.value,
                "name": p.name,
                "monthly_price_eur": p.monthly_price_eur,
                "member_cap": p.member_cap,
                "branches": p.branches,
                "features": list(p.features),
                "is_custom": p.is_custom,
            }
            for p in BILLING_PLANS
        ]
    }


@router.get("/workspace/{slug}")
async def resolve_workspace_endpoint(
    slug: str,
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Resolve a workspace by slug. Used by the login flow: the user enters
    their workspace name, we look it up, then show them the login form
    scoped to that workspace.

    Returns 404 if the slug isn't known. Returns 'pending' status if the
    workspace exists but isn't activated yet so the UI can show a
    helpful message instead of a generic error.
    """
    from app.models.tenant import Tenant
    from sqlalchemy import select

    result = await db.execute(select(Tenant).where(Tenant.slug == slug))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=404, detail="workspace_not_found")
    return {
        "slug": tenant.slug,
        "name": tenant.name,
        "is_active": tenant.is_active,
    }


@router.get("/discount")
async def discount_endpoint(db: AsyncSession = Depends(get_session)) -> dict:
    """Returns current state of the signup_discount feature flag.

    Used by the landing page to show/hide promotional copy.
    """
    flag = await get_flag(db, "signup_discount")
    if flag is None or not flag.enabled:
        return {"active": False}
    return {
        "active": True,
        "percent": flag.settings.get("percent"),
        "message": flag.settings.get("message"),
    }
