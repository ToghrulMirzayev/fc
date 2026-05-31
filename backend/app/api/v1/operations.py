"""Plans, payments, check-ins routers."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.billing_plans import get_billing_plan, tier_at_least
from app.core.deps import get_current_user
from app.core.tenant import require_current_tenant
from app.db.session import get_session
from app.models.member import Member
from app.models.membership import Membership
from app.models.plan import MembershipPlan, PlanType
from app.models.signup import BillingPlanTier
from app.models.tenant import Tenant
from app.models.user import User
from app.services.discount import SCOPE_PAYMENTS, get_discount
from app.models.visit import CheckinMethod, Payment, PaymentSource, Visit
from app.schemas.member import PlanCreate, PlanOut
from app.services.checkin import CheckinError, checkin_via_qr, record_visit
from app.services.member import initials_of
from app.services.payment import OPERATIONAL_METHODS, record_cash_payment

plans_router = APIRouter(prefix="/plans", tags=["plans"])
payments_router = APIRouter(prefix="/payments", tags=["payments"])
checkins_router = APIRouter(prefix="/checkins", tags=["checkins"])


# ─────── Plans ───────


@plans_router.get("", response_model=list[PlanOut])
async def list_plans(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[PlanOut]:
    tenant_id = require_current_tenant()
    result = await db.execute(
        select(MembershipPlan)
        .where(MembershipPlan.tenant_id == tenant_id, MembershipPlan.is_active.is_(True))
        .order_by(MembershipPlan.name)
    )
    return [PlanOut.model_validate(p) for p in result.scalars()]


@plans_router.post("", response_model=PlanOut, status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: PlanCreate,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> PlanOut:
    tenant_id = require_current_tenant()
    plan = MembershipPlan(
        tenant_id=tenant_id,
        name=payload.name,
        type=PlanType(payload.type),
        price=payload.price,
        duration_days=payload.duration_days,
        visit_limit=payload.visit_limit,
        max_freeze_days=payload.max_freeze_days,
        max_freeze_count=payload.max_freeze_count,
    )
    db.add(plan)
    await db.flush()
    return PlanOut.model_validate(plan)


# ─────── Payments ───────


class CashPaymentIn(BaseModel):
    member_id: UUID
    membership_id: UUID | None = None
    amount: Decimal
    note: str | None = None


# Each non-cash method unlocks at a specific pricing tier. Cash has no
# requirement (available on every plan, including the free trial).
_PAYMENT_METHODS: tuple[dict, ...] = (
    {
        "key": "cash",
        "label": "Cash",
        "description": "Mark a payment received in cash at the front desk.",
        "required_tier": None,
    },
    {
        "key": "card_terminal",
        "label": "Card / Apple Pay / Google Pay",
        "description": "In-person card and wallet payments via an attached terminal.",
        "required_tier": BillingPlanTier.BASIC,
    },
    {
        "key": "bank_transfer",
        "label": "Bank Transfer",
        "description": "Reconcile incoming bank transfers automatically.",
        "required_tier": BillingPlanTier.ADVANCED,
    },
    {
        "key": "online",
        "label": "Online Checkout",
        "description": "Self-serve online checkout for members.",
        "required_tier": BillingPlanTier.ADVANCED,
    },
)


@payments_router.get("/methods")
async def list_payment_methods(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Available payment methods for the tenant's current plan.

    Each method reports whether it's available on the current plan and, if
    not, which tier unlocks it and how much that upgrade costs (with the
    active "payments" discount, configured in the discounts table, applied).
    The frontend renders the locked ones dimmed with a lock and an upgrade
    popup.
    """
    tenant_id = require_current_tenant()
    tenant = await db.get(Tenant, tenant_id)
    have_tier = tenant.billing_tier if tenant else BillingPlanTier.FREE

    discount = await get_discount(db, SCOPE_PAYMENTS)
    discount_out = (
        {"percent": discount.percent, "label": discount.label}
        if discount
        else None
    )

    methods = []
    for m in _PAYMENT_METHODS:
        required: BillingPlanTier | None = m["required_tier"]
        operational = required is None or tier_at_least(have_tier, required)

        upgrade = None
        if not operational and required is not None:
            plan = get_billing_plan(required)
            original = float(plan.monthly_price_eur)
            discounted = discount.apply(original) if discount else original
            upgrade = {
                "required_tier": required.value,
                "plan_name": plan.name,
                "monthly_price_eur": plan.monthly_price_eur,
                "discounted_price_eur": discounted,
                "discount_percent": discount.percent if discount else 0,
                "discount_label": discount.label if discount else None,
            }

        methods.append(
            {
                "key": m["key"],
                "label": m["label"],
                "description": m["description"],
                "operational": operational,
                "upgrade": upgrade,
            }
        )

    return {
        "current_tier": have_tier.value,
        "discount": discount_out,
        "methods": methods,
    }


@payments_router.post("/cash", status_code=status.HTTP_201_CREATED)
async def record_cash_endpoint(
    payload: CashPaymentIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    tenant_id = require_current_tenant()
    member = await db.get(Member, payload.member_id)
    if member is None or member.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Member not found")

    membership = None
    if payload.membership_id:
        membership = await db.get(Membership, payload.membership_id)
        if membership is None or membership.member_id != member.id:
            raise HTTPException(status_code=400, detail="Membership mismatch")

    payment = await record_cash_payment(
        db,
        member=member,
        membership=membership,
        amount=payload.amount,
        note=payload.note,
        actor_user_id=user.id,
    )
    return {
        "payment_id": str(payment.id),
        "membership_activated": (membership.is_paid if membership else False),
    }


@payments_router.get("/members/{member_id}")
async def list_member_payments(
    member_id: UUID,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    tenant_id = require_current_tenant()
    result = await db.execute(
        select(Payment)
        .where(Payment.tenant_id == tenant_id, Payment.member_id == member_id)
        .order_by(Payment.paid_at.desc())
        .limit(50)
    )
    payments = result.scalars().all()
    return {
        "items": [
            {
                "id": str(p.id),
                "amount": str(p.amount),
                "currency": p.currency,
                "source": p.source.value,
                "note": p.note,
                "paid_at": p.paid_at.isoformat(),
            }
            for p in payments
        ]
    }


# ─────── Check-ins ───────


@checkins_router.post("/scan")
async def scan_endpoint(
    payload: dict,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    token = payload.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")
    try:
        visit, membership, member = await checkin_via_qr(db, token)
    except CheckinError as e:
        raise HTTPException(status_code=400, detail=e.code)
    return {
        "visit_id": str(visit.id),
        "member_id": str(member.id),
        "member_name": member.full_name,
        "initials": initials_of(member.full_name),
        "plan_name": membership.plan_name,
        "visits_remaining": membership.visits_remaining,
        "expires_on": membership.expires_on.isoformat(),
    }


@checkins_router.post("/manual/{member_id}")
async def manual_checkin(
    member_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    tenant_id = require_current_tenant()
    member = await db.get(Member, member_id)
    if member is None or member.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Member not found")
    try:
        visit, membership = await record_visit(
            db, member, CheckinMethod.MANUAL, recorded_by_user_id=user.id
        )
    except CheckinError as e:
        raise HTTPException(status_code=400, detail=e.code)
    return {
        "visit_id": str(visit.id),
        "member_name": member.full_name,
        "plan_name": membership.plan_name,
        "visits_remaining": membership.visits_remaining,
    }


@checkins_router.get("/feed")
async def feed_endpoint(
    limit: int = 50,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    tenant_id = require_current_tenant()
    result = await db.execute(
        select(Visit, Member, Membership)
        .join(Member, Visit.member_id == Member.id)
        .join(Membership, Visit.membership_id == Membership.id)
        .where(Visit.tenant_id == tenant_id)
        .order_by(Visit.checked_in_at.desc())
        .limit(limit)
    )
    items = []
    for visit, member, membership in result.all():
        items.append(
            {
                "id": str(visit.id),
                "member_id": str(member.id),
                "member_name": member.full_name,
                "initials": initials_of(member.full_name),
                "plan_name": membership.plan_name,
                "visits_remaining": membership.visits_remaining,
                "visit_limit": membership.visit_limit,
                "method": visit.method.value,
                "checked_in_at": visit.checked_in_at.isoformat(),
            }
        )
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count_result = await db.execute(
        select(Visit).where(
            Visit.tenant_id == tenant_id, Visit.checked_in_at >= today_start
        )
    )
    today_count = len(today_count_result.scalars().all())
    return {"items": items, "today_count": today_count}
