"""Pricing constants for the tiers we sell to gym operators.

Edit prices here, no DB migration needed. Frontend reads these via
the GET /api/v1/public/billing-plans endpoint, so the landing page
always shows the latest numbers.

Distinct from MembershipPlan (those are sold by gyms to their members).
"""

from dataclasses import dataclass

from app.models.signup import BillingPlanTier


@dataclass(frozen=True)
class BillingPlanInfo:
    tier: BillingPlanTier
    name: str
    monthly_price_eur: int
    member_cap: int | None  # None = unlimited
    branches: int | None
    features: tuple[str, ...]
    is_custom: bool = False  # corporate = "contact us"


BILLING_PLANS: tuple[BillingPlanInfo, ...] = (
    BillingPlanInfo(
        tier=BillingPlanTier.FREE,
        name="Free",
        monthly_price_eur=0,
        member_cap=25,
        branches=1,
        features=(
            "Up to 25 members",
            "Basic member management",
            "Telegram QR check-in",
            "30-day trial of paid features",
            "Community support",
        ),
    ),
    BillingPlanInfo(
        tier=BillingPlanTier.BASIC,
        name="Basic",
        monthly_price_eur=49,
        member_cap=150,
        branches=1,
        features=(
            "Member management",
            "QR check-in via Telegram bot",
            "Manual payments",
            "Email support",
        ),
    ),
    BillingPlanInfo(
        tier=BillingPlanTier.ADVANCED,
        name="Advanced",
        monthly_price_eur=99,
        member_cap=500,
        branches=2,
        features=(
            "Everything in Basic",
            "Class bookings",
            "Trainer accounts",
            "Renewal reminders",
            "Priority email support",
        ),
    ),
    BillingPlanInfo(
        tier=BillingPlanTier.PRO,
        name="Pro",
        monthly_price_eur=199,
        member_cap=1500,
        branches=5,
        features=(
            "Everything in Advanced",
            "Advanced analytics",
            "Custom branding",
            "Online payment integrations",
            "Phone support",
        ),
    ),
    BillingPlanInfo(
        tier=BillingPlanTier.PREMIUM,
        name="Premium",
        monthly_price_eur=399,
        member_cap=5000,
        branches=15,
        features=(
            "Everything in Pro",
            "Dedicated account manager",
            "Custom integrations",
            "SLA guarantees",
            "Onboarding training",
        ),
    ),
    BillingPlanInfo(
        tier=BillingPlanTier.CORPORATE,
        name="Corporate",
        monthly_price_eur=0,
        member_cap=None,
        branches=None,
        features=(
            "Unlimited members and branches",
            "Multi-gym dashboards",
            "Custom contracts and SLAs",
            "On-premise option",
            "24/7 dedicated support",
        ),
        is_custom=True,
    ),
)


def get_billing_plan(tier: BillingPlanTier) -> BillingPlanInfo:
    for plan in BILLING_PLANS:
        if plan.tier == tier:
            return plan
    raise KeyError(f"Unknown billing tier: {tier}")
