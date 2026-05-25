"""Public signup flow.

Creates a SignupRequest and a locked (is_active=False) Tenant. The
operator activates the tenant from the super-admin panel after review.
The slug becomes the tenant's subdomain.
"""

import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signup import (
    BillingPlanTier,
    SignupRequest,
    SignupRequestStatus,
)
from app.models.tenant import Tenant
from app.services.feature_flag import get_flag


class SignupError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass
class SignupResult:
    request_id: str
    tenant_slug: str
    tenant_url: str
    welcome_message: str
    discount_active: bool


def slugify(name: str) -> str:
    """Conservative slug: lowercase ASCII letters, digits, hyphens.

    Used as the tenant subdomain. Length-capped to 32.
    """
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")[:32]
    return s or "gym"


async def _unique_slug(db: AsyncSession, base: str) -> str:
    """Append -2, -3, ... if base is taken."""
    candidate = base
    i = 2
    while True:
        result = await db.execute(select(Tenant).where(Tenant.slug == candidate))
        if result.scalar_one_or_none() is None:
            return candidate
        candidate = f"{base}-{i}"
        i += 1


async def submit_signup(
    db: AsyncSession,
    *,
    full_name: str,
    email: str,
    phone: str,
    company_name: str,
    country: str,
    city: str | None,
    estimated_members: str,
    interested_tier: str,
    notes: str | None,
    app_domain: str,
) -> SignupResult:
    try:
        tier_enum = BillingPlanTier(interested_tier)
    except ValueError as e:
        raise SignupError("invalid_tier") from e

    # One request per email — prevent duplicate submissions.
    existing = await db.execute(
        select(SignupRequest).where(SignupRequest.email == email)
    )
    if existing.scalar_one_or_none() is not None:
        raise SignupError("email_already_submitted")

    slug = await _unique_slug(db, slugify(company_name))

    tenant = Tenant(
        slug=slug,
        name=company_name,
        currency="EUR",
        default_locale="en",
        is_active=False,
    )
    db.add(tenant)
    await db.flush()

    request = SignupRequest(
        tenant_id=tenant.id,
        full_name=full_name,
        email=email,
        phone=phone,
        company_name=company_name,
        country=country,
        city=city,
        estimated_members=estimated_members,
        interested_tier=tier_enum,
        notes=notes,
        status=SignupRequestStatus.PENDING,
    )
    db.add(request)
    await db.flush()

    # Discount welcome message — driven by signup_discount feature flag.
    flag = await get_flag(db, "signup_discount")
    discount_active = False
    welcome_lines = [
        f"Thanks, {full_name.split()[0]}! We received your request for {company_name}.",
        f"Your dedicated workspace is reserved at https://{slug}.{app_domain}.",
        "Our team will review your application and reach out within 1-2 business days "
        "with onboarding instructions.",
    ]
    if flag and flag.enabled:
        discount_active = True
        percent = flag.settings.get("percent", "10")
        message = flag.settings.get(
            "message",
            f"Sign up now and get {percent}% off your first 3 months.",
        )
        # Inject the dynamic percent into a templated message if needed.
        message = message.replace("{percent}", percent)
        welcome_lines.insert(
            1,
            f"🎉 Special offer: {message}",
        )

    return SignupResult(
        request_id=str(request.id),
        tenant_slug=slug,
        tenant_url=f"https://{slug}.{app_domain}",
        welcome_message="\n\n".join(welcome_lines),
        discount_active=discount_active,
    )
