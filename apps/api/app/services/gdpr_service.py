"""Tenant-scoped GDPR export, anonymization, and retention service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.client import ClientConsent, ClientProfile, ConsentStatus
from app.models.event import EventRecord
from app.models.session import ClientSession
from app.schemas.gdpr import GdprDeleteResponse, GdprExportResponse, GdprRetainResponse

RAW_EXPORT_KEYS = {
    "access_token",
    "debug_json",
    "internal_state",
    "password",
    "raw_debug",
    "result_payload_json",
}


class GdprService:
    """Build GDPR exports and perform reversible-safe anonymization actions."""

    async def export(
        self,
        client_id: UUID,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> GdprExportResponse:
        client = await self._get_client_or_404(client_id, tenant_id, db)
        consents = list(
            (
                await db.execute(
                    select(ClientConsent)
                    .where(
                        ClientConsent.tenant_id == tenant_id,
                        ClientConsent.client_id == client_id,
                    )
                    .order_by(ClientConsent.created_at, ClientConsent.id)
                )
            )
            .scalars()
            .all()
        )
        sessions = list(
            (
                await db.execute(
                    select(ClientSession)
                    .where(
                        ClientSession.tenant_id == tenant_id,
                        ClientSession.client_id == client_id,
                    )
                    .order_by(ClientSession.started_at, ClientSession.id)
                )
            )
            .scalars()
            .all()
        )
        session_ids = [client_session.id for client_session in sessions]
        event_conditions = [
            EventRecord.resource_id == str(client_id),
        ]
        if session_ids:
            event_conditions.append(EventRecord.session_id.in_(session_ids))
        events = list(
            (
                await db.execute(
                    select(EventRecord)
                    .where(
                        EventRecord.tenant_id == tenant_id,
                        or_(*event_conditions),
                    )
                    .order_by(EventRecord.occurred_at, EventRecord.id)
                )
            )
            .scalars()
            .all()
        )

        await self._append_audit_event(
            db=db,
            tenant_id=tenant_id,
            action="gdpr_export",
            client_id=client_id,
            metadata_json={
                "consent_count": len(consents),
                "session_count": len(sessions),
                "event_count": len(events),
            },
        )
        await db.commit()
        return GdprExportResponse(
            client_id=client_id,
            tenant_id=tenant_id,
            exported_at=datetime.now(UTC),
            profile={
                "id": str(client.id),
                "display_name": client.display_name,
                "client_code": client.client_code,
                "status": self._enum_value(client.status),
                "created_at": client.created_at,
                "updated_at": client.updated_at,
                "consents": [self._consent_dict(consent) for consent in consents],
            },
            sessions=[self._session_dict(client_session) for client_session in sessions],
            events=[self._event_dict(event) for event in events],
        )

    async def anonymize(
        self,
        client_id: UUID,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> GdprDeleteResponse:
        client = await self._get_client_or_404(client_id, tenant_id, db)
        now = datetime.now(UTC)
        client.display_name = f"ANONYMIZED-{str(uuid4())[:8]}"
        client.client_code = None
        client.updated_by_user_id = None
        await db.execute(
            update(ClientConsent)
            .where(
                ClientConsent.tenant_id == tenant_id,
                ClientConsent.client_id == client_id,
            )
            .values(status=ConsentStatus.REVOKED, revoked_at=now)
        )
        await db.execute(
            update(ClientSession)
            .where(
                ClientSession.tenant_id == tenant_id,
                ClientSession.client_id == client_id,
            )
            .values(status="anonymized", ended_at=now, updated_by_user_id=None)
        )
        await self._append_audit_event(
            db=db,
            tenant_id=tenant_id,
            action="gdpr_anonymize",
            client_id=client_id,
            metadata_json={
                "fields_anonymized": [
                    "display_name",
                    "client_code",
                    "consents",
                    "sessions",
                ],
            },
        )
        await db.commit()
        return GdprDeleteResponse(
            client_id=client_id,
            anonymized_at=now,
            fields_anonymized=["display_name", "client_code", "consents", "sessions"],
        )

    async def retain(
        self,
        client_id: UUID,
        tenant_id: UUID,
        reason: str,
        db: AsyncSession,
    ) -> GdprRetainResponse:
        await self._get_client_or_404(client_id, tenant_id, db)
        retained_until = datetime.now(UTC) + timedelta(days=365)
        await self._append_audit_event(
            db=db,
            tenant_id=tenant_id,
            action="gdpr_retain",
            client_id=client_id,
            metadata_json={
                "retained_until": retained_until.isoformat(),
                "reason": reason,
            },
        )
        await db.commit()
        return GdprRetainResponse(
            client_id=client_id,
            retained_until=retained_until,
            reason=reason,
        )

    async def _get_client_or_404(
        self,
        client_id: UUID,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> ClientProfile:
        client = await db.scalar(
            select(ClientProfile).where(
                ClientProfile.id == client_id,
                ClientProfile.tenant_id == tenant_id,
            )
        )
        if client is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        return client

    def _consent_dict(self, consent: ClientConsent) -> dict[str, Any]:
        return {
            "id": str(consent.id),
            "purpose": self._enum_value(consent.purpose),
            "status": self._enum_value(consent.status),
            "consent_text_version": consent.consent_text_version,
            "granted_at": consent.granted_at,
            "revoked_at": consent.revoked_at,
            "expires_at": consent.expires_at,
        }

    def _session_dict(self, client_session: ClientSession) -> dict[str, Any]:
        return {
            "id": str(client_session.id),
            "status": self._enum_value(client_session.status),
            "started_at": client_session.started_at,
            "ended_at": client_session.ended_at,
        }

    def _event_dict(self, event: EventRecord) -> dict[str, Any]:
        return {
            "id": str(event.id),
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "occurred_at": event.occurred_at,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "payload_json": self._filter_payload(event.payload_json),
        }

    def _filter_payload(self, payload: Any) -> Any:
        if isinstance(payload, dict):
            return {
                key: self._filter_payload(value)
                for key, value in payload.items()
                if key not in RAW_EXPORT_KEYS
            }
        if isinstance(payload, list):
            return [self._filter_payload(item) for item in payload]
        return payload

    def _enum_value(self, value: Any) -> Any:
        return value.value if hasattr(value, "value") else value

    async def _append_audit_event(
        self,
        *,
        db: AsyncSession,
        tenant_id: UUID,
        action: str,
        client_id: UUID,
        metadata_json: dict[str, Any],
    ) -> None:
        await db.execute(
            insert(AuditLog).values(
                tenant_id=tenant_id,
                actor_user_id=None,
                action=action,
                resource_type="client_profile",
                resource_id=str(client_id),
                reason=action,
                metadata_json=metadata_json,
                correlation_id=str(uuid4()),
            )
        )
