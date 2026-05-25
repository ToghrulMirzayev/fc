"""Feature flag service.

Lookup pattern:
    flag = await get_flag(db, "signup_discount", tenant_id=None)
    if flag and flag.enabled:
        percent = flag.settings.get("percent")
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feature_flag import FeatureFlag, FeatureFlagSetting


@dataclass
class ResolvedFlag:
    key: str
    enabled: bool
    settings: dict[str, str]
    description: str | None = None


async def get_flag(
    db: AsyncSession, key: str, tenant_id: UUID | None = None
) -> ResolvedFlag | None:
    """Resolve a flag.

    Tries tenant-specific override first, then falls back to global.
    """
    # Try tenant-specific
    flag: FeatureFlag | None = None
    if tenant_id is not None:
        result = await db.execute(
            select(FeatureFlag).where(
                FeatureFlag.key == key,
                FeatureFlag.tenant_id == tenant_id,
            )
        )
        flag = result.scalar_one_or_none()

    if flag is None:
        result = await db.execute(
            select(FeatureFlag).where(
                FeatureFlag.key == key, FeatureFlag.tenant_id.is_(None)
            )
        )
        flag = result.scalar_one_or_none()

    if flag is None:
        return None

    settings_result = await db.execute(
        select(FeatureFlagSetting).where(
            FeatureFlagSetting.feature_flag_id == flag.id
        )
    )
    settings = {s.setting_key: s.setting_value for s in settings_result.scalars()}

    return ResolvedFlag(
        key=flag.key,
        enabled=flag.enabled,
        settings=settings,
        description=flag.description,
    )
