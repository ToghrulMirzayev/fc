"""Seed demo data for local dev.

Usage:
    docker compose exec api python -m app.scripts.seed_dev

Creates:
- Demo tenant "Fitness Court Demo" (slug: demo), is_active=True
- Owner user: demo@fitnesscourt.com / password "demo12345"
- 4 plans
- 12 members (mostly active+paid, a couple awaiting payment, one frozen)
- Historical visits over the last 14 days
- A few payments
- Feature flag: signup_discount, ENABLED with 15% off (so the landing
  page shows the promo out of the box for local testing)

Idempotent: re-running deletes the demo tenant's data first.
"""

import asyncio
import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.security import hash_password
from app.db.provision import drop_tenant_schema, provision_tenant_schema
from app.db.session import SessionLocal, engine, tenant_session
from app.models.feature_flag import FeatureFlag, FeatureFlagSetting
from app.models.member import Member, MemberStatus
from app.models.membership import Membership, MembershipStatus
from app.models.plan import MembershipPlan, PlanType
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.visit import CheckinMethod, Payment, PaymentSource, Visit

TENANT_SLUG = "demo"


async def reset_state() -> None:
    """Wipe the demo tenant and global feature flags so we start clean."""
    # Drop the demo tenant's data schema first.
    async with engine.begin() as conn:
        await drop_tenant_schema(conn, TENANT_SLUG)
    async with SessionLocal() as db:
        # Demo tenant
        result = await db.execute(select(Tenant).where(Tenant.slug == TENANT_SLUG))
        existing = result.scalar_one_or_none()
        if existing:
            await db.delete(existing)
            await db.commit()
            print(f"Deleted existing tenant {TENANT_SLUG}")

        # Global flags
        flags_q = await db.execute(
            select(FeatureFlag).where(FeatureFlag.tenant_id.is_(None))
        )
        for f in flags_q.scalars():
            await db.delete(f)
        await db.commit()


async def seed() -> None:
    await reset_state()

    # ─── Control plane (public): tenant, owner, feature flags ───
    async with SessionLocal() as db:
        tenant = Tenant(
            slug=TENANT_SLUG,
            name="Fitness Court Demo",
            currency="AZN",
            default_locale="en",
            is_active=True,
        )
        db.add(tenant)
        await db.flush()
        tenant_id = tenant.id
        print(f"Created tenant {tenant.slug} ({tenant.name})")

        owner = User(
            tenant_id=tenant_id,
            email="demo@fitnesscourt.com",
            password_hash=hash_password("demo12345"),
            full_name="Demo Owner",
            role=UserRole.OWNER,
        )
        db.add(owner)
        await db.flush()
        owner_id = owner.id
        print(f"Created owner {owner.email} (password: demo12345)")

        # ─── Global feature flag: signup discount ───
        flag = FeatureFlag(
            tenant_id=None,
            key="signup_discount",
            enabled=True,
            description="Show a discount banner on the public signup landing page.",
        )
        db.add(flag)
        await db.flush()
        db.add(
            FeatureFlagSetting(
                feature_flag_id=flag.id,
                setting_key="percent",
                setting_value="15",
            )
        )
        db.add(
            FeatureFlagSetting(
                feature_flag_id=flag.id,
                setting_key="message",
                setting_value="Sign up this month and get {percent}% off your first 3 months.",
            )
        )

        # ─── Per-tenant feature gates for the demo workspace ───
        demo_gates = {
            "bookings": True,
            "analytics": True,
            "telegram_automation": False,
            "ai_insights": False,
            "access_control": False,
        }
        for key, enabled in demo_gates.items():
            db.add(
                FeatureFlag(
                    tenant_id=tenant_id,
                    key=key,
                    enabled=enabled,
                    description=f"Demo gate for '{key}'.",
                )
            )

        await db.commit()

    # ─── Provision the demo tenant's data schema ───
    async with engine.begin() as conn:
        await provision_tenant_schema(conn, TENANT_SLUG)

    # ─── Data plane (t_demo): plans, members, memberships, visits, payments ───
    async with tenant_session(TENANT_SLUG) as db:
        # ─── Plans ───
        plans = [
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
        for p in plans:
            db.add(p)
        await db.flush()
        monthly, pack10, yearly, trial = plans
        print(f"Created {len(plans)} plans")

        # ─── Members (Azerbaijani names) ───
        # Tuples: (name, phone, plan, days_until_expiry, email, is_paid)
        member_data = [
            ("Aysel Mammadova",   "+994 50 123 4567", monthly, 2,   "aysel.m@example.az",  True),
            ("Rashad Aliyev",     "+994 51 234 5678", pack10,  3,   None,                  True),
            ("Leyla Hasanli",     "+994 55 345 6789", yearly,  227, "leyla.h@example.az",  True),
            ("Tural Quliyev",     "+994 70 456 7890", trial,   6,   None,                  True),
            ("Nigar Rzayeva",     "+994 77 567 8901", monthly, 14,  None,                  True),
            ("Elvin Babayev",     "+994 99 678 9012", yearly,  117, "elvin.b@example.az",  True),
            ("Sevda Huseynova",   "+994 50 789 0123", monthly, 25,  None,                  True),
            ("Kamran Ismayilov",  "+994 51 890 1234", pack10,  45,  "kamran@example.az",   True),
            # Awaiting payment — card locked
            ("Farid Nuriyev",     "+994 55 901 2345", monthly, 28,  None,                  False),
            ("Aynur Karimova",    "+994 70 012 3456", pack10,  58,  None,                  False),
            # Just a regular case
            ("Orxan Suleymanli",  "+994 77 123 4567", monthly, 12,  None,                  True),
            ("Gunay Pashayeva",   "+994 99 234 5678", monthly, 8,   None,                  True),
        ]
        members = []
        for full_name, phone, plan, days_from_now, email, is_paid in member_data:
            m = Member(
                tenant_id=tenant_id,
                full_name=full_name,
                phone=phone,
                email=email,
                locale="en",
                status=MemberStatus.ACTIVE if is_paid else MemberStatus.INACTIVE,
            )
            db.add(m)
            members.append((m, plan, days_from_now, is_paid))
        await db.flush()
        print(f"Created {len(members)} members")

        # ─── Memberships ───
        memberships = []
        for member, plan, days_from_now, is_paid in members:
            starts = (
                datetime.now(UTC).date()
                - timedelta(days=plan.duration_days - days_from_now)
            )
            expires = starts + timedelta(days=plan.duration_days)
            visits_remaining = (
                plan.visit_limit - random.randint(0, plan.visit_limit - 1)
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
            memberships.append(ms)
        await db.flush()

        # ─── Historical visits (only paid memberships can have visits) ───
        paid_members_with_ms = [
            (m, ms) for (m, _p, _d, is_paid), ms in zip(members, memberships) if is_paid
        ]
        for _ in range(50):
            member, membership = random.choice(paid_members_with_ms)
            when = datetime.now(UTC) - timedelta(
                days=random.randint(0, 13),
                hours=random.randint(6, 21),
                minutes=random.randint(0, 59),
            )
            db.add(
                Visit(
                    tenant_id=tenant_id,
                    member_id=member.id,
                    membership_id=membership.id,
                    method=CheckinMethod.QR,
                    checked_in_at=when,
                )
            )

        # ─── Payments (only for paid members) ───
        for (member, plan, _days, is_paid), membership in zip(members[:8], memberships[:8]):
            if not is_paid:
                continue
            db.add(
                Payment(
                    tenant_id=tenant_id,
                    member_id=member.id,
                    membership_id=membership.id,
                    amount=plan.price,
                    currency="AZN",
                    source=PaymentSource.CASH,
                    note=f"{plan.name} — cash at front desk",
                    recorded_by_user_id=owner_id,
                )
            )

        # tenant_session commits on exit.
        print("Seed complete.")
        print()
        print("Login at http://localhost:3000/login")
        print("  Email:    demo@fitnesscourt.com")
        print("  Password: demo12345")
        print()
        print("Public signup landing: http://localhost:3000/signup")


if __name__ == "__main__":
    asyncio.run(seed())
