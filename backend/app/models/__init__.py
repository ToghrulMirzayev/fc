"""Import every model here so Alembic's autogenerate sees them all."""

from app.models.audit import AuditLog, RefreshToken
from app.models.discount import Discount
from app.models.feature_flag import FeatureFlag, FeatureFlagSetting
from app.models.member import Member, MemberStatus
from app.models.membership import FreezePeriod, Membership, MembershipStatus
from app.models.plan import MembershipPlan, PlanType
from app.models.signup import BillingPlanTier, SignupRequest, SignupRequestStatus
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.visit import CheckinMethod, Payment, PaymentSource, Visit

__all__ = [
    "AuditLog",
    "BillingPlanTier",
    "CheckinMethod",
    "Discount",
    "FeatureFlag",
    "FeatureFlagSetting",
    "FreezePeriod",
    "Member",
    "MemberStatus",
    "Membership",
    "MembershipPlan",
    "MembershipStatus",
    "Payment",
    "PaymentSource",
    "PlanType",
    "RefreshToken",
    "SignupRequest",
    "SignupRequestStatus",
    "Tenant",
    "User",
    "UserRole",
    "Visit",
]
