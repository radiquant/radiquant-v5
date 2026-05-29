"""Client domain request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.client import ClientStatus, ConsentPurpose, ConsentStatus


class ClientProfileCreate(BaseModel):
    """Create a tenant-scoped human client profile."""

    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=200)
    client_code: str | None = Field(default=None, min_length=1, max_length=80)


class ClientProfileUpdate(BaseModel):
    """Update safe client profile fields only."""

    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    client_code: str | None = Field(default=None, min_length=1, max_length=80)
    status: ClientStatus | None = None

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "ClientProfileUpdate":
        if self.display_name is None and self.client_code is None and self.status is None:
            raise ValueError("at least one update field is required")
        return self


class ClientProfileResponse(BaseModel):
    """Safe client profile projection without raw/debug/internal data."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    display_name: str
    client_code: str | None
    status: ClientStatus
    created_at: datetime
    updated_at: datetime


class ClientProfileListResponse(BaseModel):
    """List response for tenant-scoped client profiles."""

    model_config = ConfigDict(extra="forbid")

    items: list[ClientProfileResponse]
    limit: int
    offset: int


class ClientConsentCreate(BaseModel):
    """Record consent for one client and purpose."""

    model_config = ConfigDict(extra="forbid")

    purpose: ConsentPurpose
    status: ConsentStatus = ConsentStatus.GRANTED
    consent_text_version: str = Field(min_length=1, max_length=80)
    expires_at: datetime | None = None


class ClientConsentResponse(BaseModel):
    """Safe consent projection."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    client_id: UUID
    purpose: ConsentPurpose
    status: ConsentStatus
    consent_text_version: str
    granted_at: datetime
    revoked_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ClientConsentListResponse(BaseModel):
    """List response for tenant-scoped client consent records."""

    model_config = ConfigDict(extra="forbid")

    items: list[ClientConsentResponse]
