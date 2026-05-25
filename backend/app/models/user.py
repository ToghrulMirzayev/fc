"""Staff users — gym owners, managers, receptionists, trainers.

Members are NOT in this table; they're in `members`. Members don't have
email/password — they authenticate to the Telegram bot via account linking.
"""

import enum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class UserRole(str, enum.Enum):
    """Role hierarchy. Higher in this list = more permissions.

    - SUPER_ADMIN: Keybit/operator level, cross-tenant. Cannot belong to a
      tenant; tenant_id is null for super admins.
    - OWNER: full access within their tenant.
    - MANAGER: everything except billing config and staff management.
    - RECEPTIONIST: check-ins, member CRUD, payments.
    - TRAINER: view their members and their classes.
    """

    SUPER_ADMIN = "super_admin"
    OWNER = "owner"
    MANAGER = "manager"
    RECEPTIONIST = "receptionist"
    TRAINER = "trainer"


class User(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "users"

    # Null for SUPER_ADMIN; required for everyone else.
    tenant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(128))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x])
    )
    is_active: Mapped[bool] = mapped_column(default=True)
