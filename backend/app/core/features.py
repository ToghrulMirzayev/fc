"""Feature catalog — the single source of truth for what can be gated.

Every gateable section or in-page capability has an entry here. The
`default_enabled` flag decides what a brand-new tenant gets with no
explicit override:

- Basics (login, dashboard, members, plans, payments, check-ins) are
  ON by default — every operator needs them to run a gym.
- Everything that maps to a higher plan tier (bookings, Telegram
  automation, analytics, AI, access-control hardware) is OFF by
  default and must be turned on per-tenant.

Resolution order (see resolve_features):
    per-tenant feature_flags row  ->  this catalog's default_enabled

The frontend HIDES anything that resolves to False — it never renders a
disabled button. The same map gates the matching backend endpoints.

Add a new gate by adding a Feature here and reading it where needed; no
migration required because the feature_flags table is generic.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.feature_flag import FeatureFlag
from app.models.user import User


@dataclass(frozen=True)
class Feature:
    key: str
    label: str
    description: str
    default_enabled: bool


# The catalog. Keys are stable strings shared with the frontend.
FEATURES: tuple[Feature, ...] = (
    # --- Basics: always on unless an operator explicitly disables them ---
    Feature(
        "dashboard",
        "Dashboard",
        "Home overview with key numbers.",
        default_enabled=True,
    ),
    Feature(
        "members",
        "Members",
        "Member directory, profiles, freeze & renew.",
        default_enabled=True,
    ),
    Feature(
        "checkins",
        "Check-ins",
        "Telegram QR / manual check-in log.",
        default_enabled=True,
    ),
    Feature(
        "plans",
        "Plans",
        "Membership plans the gym sells to its members.",
        default_enabled=True,
    ),
    Feature(
        "payments",
        "Payments",
        "Record and review member payments.",
        default_enabled=True,
    ),
    Feature(
        "configuration",
        "Configuration",
        "Workspace settings.",
        default_enabled=True,
    ),
    # --- Gated: map to higher plan tiers, off by default ---
    Feature(
        "bookings",
        "Class & PT bookings",
        "Class and personal-training booking, plus the schedule.",
        default_enabled=False,
    ),
    Feature(
        "telegram_automation",
        "Telegram automation",
        "Automated reminders, confirmations and broadcasts.",
        default_enabled=False,
    ),
    Feature(
        "analytics",
        "Advanced analytics",
        "Advanced analytics dashboard and reports.",
        default_enabled=False,
    ),
    Feature(
        "ai_insights",
        "AI insights",
        "Churn prediction and AI assistant for staff.",
        default_enabled=False,
    ),
    Feature(
        "access_control",
        "Access control",
        "Turnstile / access-control hardware management.",
        default_enabled=False,
    ),
)

FEATURE_KEYS: frozenset[str] = frozenset(f.key for f in FEATURES)
_DEFAULTS: dict[str, bool] = {f.key: f.default_enabled for f in FEATURES}


async def resolve_features(
    db: AsyncSession, tenant_id: UUID | None
) -> dict[str, bool]:
    """Return {feature_key: enabled} for a tenant.

    Starts from catalog defaults, then applies any per-tenant
    feature_flags row whose key matches a known feature. One query.
    """
    resolved = dict(_DEFAULTS)
    if tenant_id is None:
        return resolved

    result = await db.execute(
        select(FeatureFlag).where(
            FeatureFlag.tenant_id == tenant_id,
            FeatureFlag.key.in_(FEATURE_KEYS),
        )
    )
    for flag in result.scalars():
        resolved[flag.key] = flag.enabled
    return resolved


def require_feature(key: str) -> Callable[..., Awaitable[User]]:
    """Dependency factory: 403 unless `key` is enabled for the tenant.

    Backend mirror of the frontend gate — so a hidden section can't be
    reached by hitting the API directly.

    Usage:
        @router.get(
            "/reports",
            dependencies=[Depends(require_feature("analytics"))],
        )
    """

    async def _check(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_session),
    ) -> User:
        features = await resolve_features(db, user.tenant_id)
        if not features.get(key, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="feature_not_available",
            )
        return user

    return _check
