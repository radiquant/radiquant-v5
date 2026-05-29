"""Authentication request/response schemas."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.identity import RoleName


class LoginRequest(BaseModel):
    """Tenant-scoped login request."""

    model_config = ConfigDict(extra="forbid")

    tenant_slug: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class TokenResponse(BaseModel):
    """Bearer token response for authenticated identity sessions."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
    tenant_id: UUID
    user_id: UUID
    role: RoleName


class LogoutResponse(BaseModel):
    """Logout acknowledgement."""

    model_config = ConfigDict(extra="forbid")

    status: str = "ok"
