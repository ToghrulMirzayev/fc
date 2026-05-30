"""Auth request/response schemas."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    refresh_token: str


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
