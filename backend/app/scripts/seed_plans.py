"""Seed one demo company (tenant) per billing plan tier.

So you can log into each and see how the product looks on FREE, BASIC,
ADVANCED, PRO, PREMIUM and CORPORATE — feature gates, member volume and
plans scale per tier.

Multi-tenancy: control-plane rows (tenant, owner user, feature flags,
signup request) go into the shared ``public`` schema; each tenant's domain
data (plans, members, memberships, visits, payments) is created inside its
own schema ``t_<slug>`` via app.db.provision. Each tenant gets exactly one
user — the owner.

Usage:
    docker compose exec api python -m app.scripts.seed_plans

Idempotent: re-running drops each seeded tenant's schema and deletes the
public tenant row first.
"""

import asyncio
import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.billing_plans import BILLING_PLANS, get_billing_plan
from app.core.security import hash_password
from app.db.provision import drop_tenant_schema, provision_tenant_schema
from app.db.session import SessionLocal, engine, tenant_session
from app.models.discount import Discount
from app.models.feature_flag import FeatureFlag
from app.models.member import Member, MemberStatus
from app.models.membership import Membership, MembershipStatus
from app.models.plan import MembershipPlan, PlanType
from app.models.signup import (
    BillingPlanTier,
    SignupRequest,
    SignupRequestStatus,
)
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.visit import CheckinMethod, Payment, PaymentSource, Visit

# Gated feature keys (see app/core/features.py). Basics are always on.
GATED_KEYS = (
    "bookings",
    "telegram_automation",
    "analytics",
    "ai_insights",
    "access_control",
)

# Which gated features each tier unlocks, derived from billing_plans.py.
TIER_GATES: dict[BillingPlanTier, set[str]] = {
    BillingPlanTier.FREE: set(),
    BillingPlanTier.BASIC: set(),
    BillingPlanTier.ADVANCED: {"bookings", "telegram_automation", "analytics"},
    BillingPlanTier.PRO: set(GATED_KEYS),
    BillingPlanTier.PREMIUM: set(GATED_KEYS),
    BillingPlanTier.CORPORATE: set(GATED_KEYS),
}

# How many demo members to seed per tier (a readable sample, not the cap).
TIER_MEMBER_COUNT: dict[BillingPlanTier, int] = {
    BillingPlanTier.FREE: 6,
    BillingPlanTier.BASIC: 10,
    BillingPlanTier.ADVANCED: 16,
    BillingPlanTier.PRO: 24,
    BillingPlanTier.PREMIUM: 30,
    BillingPlanTier.CORPORATE: 36,
}

# Pools for generating member names/phones.
FIRST_NAMES = [
    "Aysel", "Rashad", "Leyla", "Tural", "Nigar", "Elvin", "Sevda",
    "Kamran", "Farid", "Aynur", "Orxan", "Gunay", "Murad", "Lala",
    "Vusal", "Aytac", "Ramin", "Narmin", "Elnur", "Zaur", "Sabina",
    "Ilkin", "Gulnar", "Anar",
]
LAST_NAMES = [
    "Mammadova", "Aliyev", "Hasanli", "Quliyev", "Rzayeva", "Babayev",
    "Huseynova", "Ismayilov", "Nuriyev", "Karimova", "Suleymanli",
    "Pashayeva", "Aghayev", "Valiyeva", "Guliyev",
]


async def reset_state(slugs: list[str]) -> None:
    """Drop each tenant's data schema, then delete the public tenant rows."""
    async with engine.begin() as conn:
        for slug in slugs:
            await drop_tenant_schema(conn, slug)
    async with SessionLocal() as db:
        result = await db.execute(select(Tenant).where(Tenant.slug.in_(slugs)))
        for tenant in result.scalars():
            await db.delete(tenant)
            print(f"Deleted existing tenant {tenant.slug}")
        await db.commit()


def build_plans(tenant_id) -> list[MembershipPlan]:
    return [
        MembershipPlan(
            tenant_id=tenant_id,
            name="Monthly Unlimited",
            type=PlanType.UNLIMITED_MONTHLY,
            price=80,
            duration_days=30,
            visit_limit=None,
        ),
        MembershipPlan(
            tenant_id=tenant_id,
            name="10-visit pack",
            type=PlanType.LIMITED_VISITS,
            price=60,
            duration_days=60,
            visit_limit=10,
        ),
        MembershipPlan(
            tenant_id=tenant_id,
            name="Yearly Premium",
            type=PlanType.YEARLY,
            price=800,
            duration_days=365,
            visit_limit=None,
        ),
        MembershipPlan(
            tenant_id=tenant_id,
            name="Trial 7-day",
            type=PlanType.TRIAL,
            price=0,
            duration_days=7,
            visit_limit=None,
        ),
    ]


async def seed_control_plane(db, tier: BillingPlanTier):
    """Create the public-schema rows: tenant, owner user, flags, signup.

    Returns (tenant_id, owner_id, slug, unlocked_features).
    """
    info = get_billing_plan(tier)
    slug = f"plan-{tier.value}"

    tenant = Tenant(
        slug=slug,
        name=f"{info.name} Gym ({info.name} plan)",
        currency="AZN",
        default_locale="en",
        is_active=True,
        billing_tier=tier,
    )
    db.add(tenant)
    await db.flush()

    owner = User(
        tenant_id=tenant.id,
        email=f"{tier.value}@fitnesscourt.com",
        password_hash=hash_password("demo12345"),
        full_name=f"{info.name} Owner",
        role=UserRole.OWNER,
    )
    db.add(owner)
    await db.flush()

    # Feature gates for this tier.
    unlocked = TIER_GATES[tier]
    for key in GATED_KEYS:
        db.add(
            FeatureFlag(
                tenant_id=tenant.id,
                key=key,
                enabled=key in unlocked,
                description=f"{info.name} plan gate for '{key}'.",
            )
        )

    # Signup request so the super-admin panel shows the company.
    db.add(
        SignupRequest(
            tenant_id=tenant.id,
            full_name=owner.full_name,
            email=owner.email,
            phone="+994 50 000 0000",
            company_name=tenant.name,
            country="Azerbaijan",
            city="Baku",
            estimated_members=str(info.member_cap or "1000+"),
            interested_tier=tier,
            notes="Seeded demo company for plan preview.",
            status=SignupRequestStatus.ACTIVATED,
        )
    )

    return tenant.id, owner.id, slug, unlocked


async def seed_data_plane(
    tenant_id, owner_id, slug: str, tier: BillingPlanTier
) -> None:
    """Seed the per-tenant schema: plans, members, memberships, visits,
    payments. Runs in a session pinned to t_<slug>."""
    count = TIER_MEMBER_COUNT[tier]
    rng = random.Random(f"seed-{tier.value}")  # deterministic per tier

    async with tenant_session(slug) as db:
        plans = build_plans(tenant_id)
        for p in plans:
            db.add(p)
        await db.flush()

        paid_pairs = []
        for i in range(count):
            plan = rng.choice(plans)
            is_paid = rng.random() > 0.15  # ~15% awaiting payment
            full_name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
            member = Member(
                tenant_id=tenant_id,
                full_name=full_name,
                phone=f"+994 {rng.randint(50, 99)} {rng.randint(100, 999)} "
                f"{rng.randint(1000, 9999)}",
                email=(
                    f"{full_name.split()[0].lower()}{i}@example.az"
                    if rng.random() > 0.5
                    else None
                ),
                locale="en",
                status=MemberStatus.ACTIVE if is_paid else MemberStatus.INACTIVE,
            )
            db.add(member)
            await db.flush()

            days_from_now = rng.randint(1, plan.duration_days - 1)
            starts = datetime.now(UTC).date() - timedelta(
                days=plan.duration_days - days_from_now
            )
            expires = starts + timedelta(days=plan.duration_days)
            visits_remaining = (
                plan.visit_limit - rng.randint(0, plan.visit_limit - 1)
                if plan.visit_limit
                else None
            )
            ms = Membership(
                tenant_id=tenant_id,
                member_id=member.id,
                plan_id=plan.id,
                plan_name=plan.name,
                plan_type=plan.type,
                price=plan.price,
                starts_on=starts,
                expires_on=expires,
                visit_limit=plan.visit_limit,
                visits_remaining=visits_remaining,
                max_freeze_days=plan.max_freeze_days,
                max_freeze_count=plan.max_freeze_count,
                status=MembershipStatus.ACTIVE,
                is_paid=is_paid,
            )
            db.add(ms)
            await db.flush()
            if is_paid:
                paid_pairs.append((member, ms, plan))

        # Recent visits (paid members only).
        if paid_pairs:
            for _ in range(count * 4):
                member, ms, _plan = rng.choice(paid_pairs)
                when = datetime.now(UTC) - timedelta(
                    days=rng.randint(0, 13),
                    hours=rng.randint(6, 21),
                    minutes=rng.randint(0, 59),
                )
                db.add(
                    Visit(
                        tenant_id=tenant_id,
                        member_id=member.id,
                        membership_id=ms.id,
                        method=CheckinMethod.QR,
                        checked_in_at=when,
                    )
                )

        # Payments (paid members only).
        for member, ms, plan in paid_pairs:
            db.add(
                Payment(
                    tenant_id=tenant_id,
                    member_id=member.id,
                    membership_id=ms.id,
                    amount=plan.price,
                    currency="AZN",
                    source=PaymentSource.CASH,
                    note=f"{plan.name} — cash at front desk",
                    recorded_by_user_id=owner_id,
                )
            )
        # tenant_session commits on exit.


async def seed() -> None:
    slugs = [f"plan-{t.value}" for t in (p.tier for p in BILLING_PLANS)]
    await reset_state(slugs)

    print("Seeding one company per billing plan tier:")
    for info in BILLING_PLANS:
        tier = info.tier

        # 1) Control plane (public).
        async with SessionLocal() as db:
            tenant_id, owner_id, slug, unlocked = await seed_control_plane(
                db, tier
            )
            await db.commit()

        # 2) Provision the tenant's data schema.
        async with engine.begin() as conn:
            schema = await provision_tenant_schema(conn, slug)

        # 3) Data plane (t_<slug>).
        await seed_data_plane(tenant_id, owner_id, slug, tier)

        count = TIER_MEMBER_COUNT[tier]
        price = "custom" if info.is_custom else f"€{info.monthly_price_eur}/mo"
        print(
            f"  {tier.value:10s} {slug:18s} schema={schema:14s} "
            f"{count:2d} members  gates={sorted(unlocked) or 'none'}  ({price})"
        )

    # Global discount for the payments upgrade popup (scope="payments").
    async with SessionLocal() as db:
        existing = await db.execute(
            select(Discount).where(Discount.scope == "payments")
        )
        disc = existing.scalar_one_or_none()
        if disc is None:
            db.add(
                Discount(
                    scope="payments",
                    percent=20,
                    active=True,
                    label="Launch offer — 20% off your upgrade",
                )
            )
            print("  discount: payments 20% (active)")
        else:
            disc.percent = 20
            disc.active = True
            disc.label = "Launch offer — 20% off your upgrade"
            print("  discount: payments 20% (updated)")
        await db.commit()

    print()
    print("Done. Log in at http://localhost:3000/login with password 'demo12345':")
    for info in BILLING_PLANS:
        print(f"  {info.name:10s} -> {info.tier.value}@fitnesscourt.com")


if __name__ == "__main__":
    asyncio.run(seed())
