"""Auth request/response schemas."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    # The workspace the user is signing in to (slug from the URL). When
    # present, login is rejected unless the user belongs to this tenant —
    # so an admin of one gym can't log in under another gym's workspace.
    workspace_slug: str | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    refresh_token: str


class UpdateMeIn(BaseModel):
    # Both optional — the client sends only the field(s) being edited.
    full_name: str | None = Field(default=None, min_length=2, max_length=128)
    email: EmailStr | None = None


class CurrentUserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    tenant_id: UUID | None
    tenant_slug: str | None
    tenant_name: str | None
    # Resolved feature gates for this tenant: {feature_key: enabled}.
    # The frontend hides any section/action whose key is False or absent.
    features: dict[str, bool] = {}
