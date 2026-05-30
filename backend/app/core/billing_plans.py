"""Pricing constants for the tiers we sell to gym operators.

Edit prices here, no DB migration needed. Frontend reads these via
the GET /api/v1/public/billing-plans endpoint, so the landing page
always shows the latest numbers.

These plans are sold to fitness-studio OWNERS (our B2B customers), not
to the people who train at those studios. So tiers scale on operator
value — admin/trainer seats, locations, AI, analytics, Telegram
automation, and access-control hardware — not just member headcount.

Distinct from MembershipPlan (those are sold by gyms to their members).
"""

from dataclasses import dataclass

from app.models.signup import BillingPlanTier


@dataclass(frozen=True)
class BillingPlanInfo:
    tier: BillingPlanTier
    name: str
    tagline: str
    monthly_price_eur: int
    member_cap: int | None  # None = unlimited
    admin_seats: int | None  # staff/trainer logins; None = unlimited
    branches: int | None  # locations; None = unlimited
    features: tuple[str, ...]
    is_custom: bool = False  # corporate = "contact us"
    is_trial: bool = False  # free tier is always time-limited, never forever
    trial_days: int | None = None
    highlight: bool = False  # "most popular" emphasis on the landing page


BILLING_PLANS: tuple[BillingPlanInfo, ...] = (
    BillingPlanInfo(
        tier=BillingPlanTier.FREE,
        name="Trial",
        tagline="Try the full platform, on us.",
        monthly_price_eur=0,
        member_cap=50,
        admin_seats=1,
        branches=1,
        is_trial=True,
        trial_days=14,
        features=(
            "Full access for 14 days",
            "Up to 50 members",
            "1 admin seat · 1 location",
            "Telegram QR check-in",
            "Manual payments",
            "Community support",
        ),
    ),
    BillingPlanInfo(
        tier=BillingPlanTier.BASIC,
        name="Starter",
        tagline="For a new single-location studio.",
        monthly_price_eur=49,
        member_cap=200,
        admin_seats=2,
        branches=1,
        features=(
            "2 admin seats",
            "Member management + Telegram QR check-in",
            "Telegram check-in confirmations",
            "Manual & card payments",
            "Basic monthly reports",
            "Email support",
        ),
    ),
    BillingPlanInfo(
        tier=BillingPlanTier.ADVANCED,
        name="Growth",
        tagline="For growing studios with classes & staff.",
        monthly_price_eur=99,
        member_cap=600,
        admin_seats=5,
        branches=2,
        highlight=True,
        features=(
            "Everything in Starter",
            "5 admin & trainer seats · 2 locations",
            "Class & PT bookings",
            "Automated Telegram reminders (renewals, expiring passes)",
            "Online payment integrations",
            "Advanced analytics dashboard",
            "Priority email support",
        ),
    ),
    BillingPlanInfo(
        tier=BillingPlanTier.PRO,
        name="Pro",
        tagline="For multi-location gyms that want AI & automation.",
        monthly_price_eur=199,
        member_cap=2000,
        admin_seats=15,
        branches=5,
        features=(
            "Everything in Growth",
            "15 seats · 5 locations",
            "AI insights & churn prediction",
            "AI assistant for staff",
            "Telegram broadcast campaigns",
            "1 access-control / turnstile unit included",
            "Custom branding · data exports · API access",
            "Phone support",
        ),
    ),
    BillingPlanInfo(
        tier=BillingPlanTier.PREMIUM,
        name="Premium",
        tagline="For established multi-site chains.",
        monthly_price_eur=399,
        member_cap=6000,
        admin_seats=40,
        branches=15,
        features=(
            "Everything in Pro",
            "40 seats · 15 locations",
            "Up to 5 access-control / turnstile units included",
            "AI forecasting & advanced reports",
            "Dedicated account manager",
            "Onboarding & staff training",
            "SLA guarantees",
        ),
    ),
    BillingPlanInfo(
        tier=BillingPlanTier.CORPORATE,
        name="Corporate",
        tagline="For large networks & franchises.",
        monthly_price_eur=0,
        member_cap=None,
        admin_seats=None,
        branches=None,
        is_custom=True,
        features=(
            "Everything in Premium",
            "Unlimited seats, members & locations",
            "Unlimited access-control hardware & install",
            "Multi-gym & franchise dashboards",
            "Custom integrations & on-premise option",
            "Custom contracts & SLAs",
            "24/7 dedicated support",
        ),
    ),
)


def get_billing_plan(tier: BillingPlanTier) -> BillingPlanInfo:
    for plan in BILLING_PLANS:
        if plan.tier == tier:
            return plan
    raise KeyError(f"Unknown billing tier: {tier}")
