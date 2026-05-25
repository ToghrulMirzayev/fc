"""Member and membership schemas."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MembershipBrief(BaseModel):
    """Minimal membership info shown in list rows and member profiles."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_name: str
    plan_type: str
    starts_on: date
    expires_on: date
    visit_limit: int | None
    visits_remaining: int | None
    status: str
    days_left: int
    is_paid: bool


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    phone: str
    email: str | None
    telegram_user_id: int | None
    locale: str
    status: str
    notes: str | None
    active_membership: MembershipBrief | None
    initials: str  # computed server-side


class MemberCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=128)
    phone: str = Field(min_length=4, max_length=32)
    email: EmailStr | None = None
    locale: str = "en"


class MemberUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    notes: str | None = None


class MemberListItem(BaseModel):
    """Lightweight row for the members table."""

    id: UUID
    full_name: str
    phone: str
    initials: str
    status: str
    plan_name: str | None
    plan_type: str | None
    expires_on: date | None
    days_left: int | None
    visits_remaining: int | None
    visit_limit: int | None


class MemberListOut(BaseModel):
    items: list[MemberListItem]
    total: int
    counts_by_status: dict[str, int]


class LinkingCodeOut(BaseModel):
    """Returned to staff when they generate a Telegram linking code."""

    code: str
    expires_at: date  # UTC date — minutes-level not exposed to staff
    member_id: UUID


# ─────── Plans ───────


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    type: str
    price: Decimal
    duration_days: int
    visit_limit: int | None
    max_freeze_days: int
    max_freeze_count: int
    is_active: bool


class PlanCreate(BaseModel):
    name: str
    type: str  # PlanType value
    price: Decimal
    duration_days: int = 30
    visit_limit: int | None = None
    max_freeze_days: int = 30
    max_freeze_count: int = 2


# ─────── Assign plan / freeze ───────


class AssignPlanIn(BaseModel):
    plan_id: UUID
    starts_on: date | None = None  # defaults to today


class FreezeIn(BaseModel):
    ends_on: date  # planned auto-resume date
    reason: str | None = None


# ─────── Payments ───────


class PaymentCreate(BaseModel):
    amount: Decimal
    source: str  # PaymentSource value
    membership_id: UUID | None = None
    note: str | None = None


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amount: Decimal
    currency: str
    source: str
    note: str | None
    paid_at: str  # ISO datetime


# ─────── Visits ───────


class VisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    member_id: UUID
    member_name: str
    method: str
    checked_in_at: str
    plan_name: str
    visits_remaining: int | None
