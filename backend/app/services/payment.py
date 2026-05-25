"""Payment service.

In v1.0 only cash payments are operational. Other methods (bank transfer,
card via terminal, Apple Pay / Google Pay) exist as enum values for the
data model but their UI is gated behind "coming soon" placeholders.

Recording a payment for a specific membership marks it as paid, which
unlocks check-ins and switches the member's bot card from "awaiting
payment" to "active".
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.member import Member
from app.models.membership import Membership
from app.models.tenant import Tenant
from app.models.visit import Payment, PaymentSource


class PaymentError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


# Only this method is operational in v1.0. The others are visible in the
# UI as locked tabs and rejected here if attempted programmatically.
OPERATIONAL_METHODS: frozenset[PaymentSource] = frozenset({PaymentSource.CASH})


async def record_cash_payment(
    db: AsyncSession,
    *,
    member: Member,
    membership: Membership | None,
    amount: Decimal,
    note: str | None,
    actor_user_id: UUID,
) -> Payment:
    """Record a cash payment. If linked to a membership, marks it paid."""
    tenant = await db.get(Tenant, member.tenant_id)
    currency = tenant.currency if tenant else "EUR"

    payment = Payment(
        tenant_id=member.tenant_id,
        member_id=member.id,
        membership_id=membership.id if membership else None,
        amount=amount,
        currency=currency,
        source=PaymentSource.CASH,
        note=note,
        recorded_by_user_id=actor_user_id,
    )
    db.add(payment)

    if membership is not None and not membership.is_paid:
        membership.is_paid = True
        db.add(
            AuditLog(
                tenant_id=member.tenant_id,
                actor_user_id=actor_user_id,
                event="membership.activated",
                details=f"membership={membership.id} via cash payment",
            )
        )

    db.add(
        AuditLog(
            tenant_id=member.tenant_id,
            actor_user_id=actor_user_id,
            event="payment.recorded",
            details=f"member={member.id} amount={amount} {currency} source=cash",
        )
    )

    await db.flush()
    return payment
