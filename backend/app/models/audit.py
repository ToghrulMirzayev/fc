"""Audit log and refresh tokens.

Audit log records sensitive admin actions for accountability. Refresh
tokens are stored hashed so a DB leak can't be replayed.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class AuditLog(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "audit_log"

    tenant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL"), index=True, nullable=True
    )
    # Who did it. Null if system action.
    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # What kind of event. Free-form short string — e.g. "auth.login.failed",
    # "membership.freeze", "payment.recorded". Keep dotted-namespace style.
    event: Mapped[str] = mapped_column(String(64), index=True)
    # Free-form context. JSON-serialized payload.
    details: Mapped[str | None] = mapped_column(String(2000), nullable=True)


class RefreshToken(Base, UUIDPKMixin, TimestampMixin):
    """Stored refresh tokens — hashed at rest.

    On refresh: client sends raw token, server hashes and looks up, rotates
    by deleting the old row and issuing a new pair.
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
