"""Discount lookup — read promo percentages from the discounts table.

Discounts are configured by the operator as rows keyed by `scope`
(e.g. "payments"). Application code asks for a scope and gets back the
active discount, or None. Prices are never discounted unless a row exists
and is active.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discount import Discount

# Stable scope keys. Add a constant here when a new area gets a discount.
SCOPE_PAYMENTS = "payments"


@dataclass(frozen=True)
class DiscountInfo:
    scope: str
    percent: int
    label: str | None

    def apply(self, amount: float) -> float:
        """Return `amount` after this discount, rounded to 2 decimals."""
        return round(amount * (100 - self.percent) / 100, 2)


async def get_discount(db: AsyncSession, scope: str) -> DiscountInfo | None:
    """Return the active discount for `scope`, or None."""
    result = await db.execute(
        select(Discount).where(Discount.scope == scope, Discount.active.is_(True))
    )
    row = result.scalar_one_or_none()
    if row is None or row.percent <= 0:
        return None
    return DiscountInfo(scope=row.scope, percent=row.percent, label=row.label)
