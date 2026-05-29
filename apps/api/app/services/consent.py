"""Consent domain service and future processing gate primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import ClientConsent, ClientProfile, ConsentPurpose, ConsentStatus

ConsentFailureReason = Literal["missing", "revoked", "expired", "wrong_tenant"]


class ConsentRequiredError(Exception):
    """Raised when required consent is absent or not currently active.

    The public detail is intentionally generic so callers do not reveal whether a
    client exists in another tenant or which consent state failed.
    """

    public_detail = "Consent required"

    def __init__(self, reason: ConsentFailureReason) -> None:
        super().__init__(self.public_detail)
        self.reason = reason


@dataclass(frozen=True)
class ConsentCheckResult:
    """Safe result for an active consent assertion."""

    consent_id: UUID
    tenant_id: UUID
    client_id: UUID
    purpose: ConsentPurpose
    consent_text_version: str


class ConsentService:
    """Evaluate tenant-scoped consent state for future sensitive processing."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def assert_active_consent(
        self,
        *,
        tenant_id: UUID,
        client_id: UUID,
        purpose: ConsentPurpose,
        now: datetime | None = None,
    ) -> ConsentCheckResult:
        """Assert a tenant-owned client has current granted consent for a purpose."""
        check_time = now or datetime.now(UTC)
        client_exists = await self.session.scalar(
            select(ClientProfile.id).where(ClientProfile.id == client_id, ClientProfile.tenant_id == tenant_id)
        )
        if client_exists is None:
            raise ConsentRequiredError("wrong_tenant")

        consent = await self.session.scalar(
            select(ClientConsent)
            .where(
                ClientConsent.tenant_id == tenant_id,
                ClientConsent.client_id == client_id,
                ClientConsent.purpose == purpose,
            )
            .order_by(ClientConsent.created_at.desc(), ClientConsent.granted_at.desc(), ClientConsent.id.desc())
            .limit(1)
        )
        if consent is None:
            raise ConsentRequiredError("missing")
        if consent.status != ConsentStatus.GRANTED or consent.revoked_at is not None:
            raise ConsentRequiredError("revoked")
        expires_at = consent.expires_at
        if expires_at is not None:
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
            if check_time.tzinfo is None:
                check_time = check_time.replace(tzinfo=UTC)
            if expires_at <= check_time:
                raise ConsentRequiredError("expired")

        return ConsentCheckResult(
            consent_id=consent.id,
            tenant_id=consent.tenant_id,
            client_id=consent.client_id,
            purpose=consent.purpose,
            consent_text_version=consent.consent_text_version,
        )

    async def assert_analysis_allowed(
        self,
        *,
        tenant_id: UUID,
        client_id: UUID,
        now: datetime | None = None,
    ) -> ConsentCheckResult:
        """Future analysis gate: analysis requires active analysis consent."""
        return await self.assert_active_consent(
            tenant_id=tenant_id,
            client_id=client_id,
            purpose=ConsentPurpose.ANALYSIS,
            now=now,
        )
