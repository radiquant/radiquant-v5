"""Feature-flagged HRV coherence gate for harmonization jobs."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.event import EventRecord
from app.schemas.hrv import HRVGateResult, HRVReading

HRV_COHERENCE_THRESHOLD = float(os.getenv("RQ5_HRV_COHERENCE_THRESHOLD", "0.35"))
FEATURE_HRV_ENABLED = os.getenv("RQ5_FEATURE_HRV", "false").lower() == "true"


class HRVGateService:
    """Evaluate the optional HRV coherence gate before harmonization start."""

    async def evaluate(
        self,
        session_id: UUID,
        tenant_id: UUID,
        therapist_override: bool = False,
        db: AsyncSession | None = None,
    ) -> HRVGateResult:
        if FEATURE_HRV_ENABLED is False:
            result = HRVGateResult(
                passed=True,
                coherence_score=HRV_COHERENCE_THRESHOLD,
                threshold=HRV_COHERENCE_THRESHOLD,
                override_by_therapist=therapist_override,
            )
            if db is not None:
                await self._append_audit_event(db, tenant_id, session_id, result)
                await db.commit()
            return result

        reading = await self._latest_reading(session_id, tenant_id, db)
        passed = reading.coherence_score >= HRV_COHERENCE_THRESHOLD or therapist_override
        result = HRVGateResult(
            passed=passed,
            coherence_score=reading.coherence_score,
            threshold=HRV_COHERENCE_THRESHOLD,
            override_by_therapist=therapist_override,
        )
        if db is not None:
            await self._append_audit_event(db, tenant_id, session_id, result)
            await db.commit()
        return result

    async def _latest_reading(
        self,
        session_id: UUID,
        tenant_id: UUID,
        db: AsyncSession | None,
    ) -> HRVReading:
        if db is not None:
            record = await db.scalar(
                select(EventRecord)
                .where(
                    EventRecord.tenant_id == tenant_id,
                    EventRecord.session_id == session_id,
                    EventRecord.event_type.in_(("hrv.reading", "hrv_reading")),
                )
                .order_by(EventRecord.occurred_at.desc(), EventRecord.created_at.desc())
            )
            if record is not None:
                return HRVReading.model_validate(record.payload_json)
        return HRVReading(
            heart_rate_bpm=72.0,
            coherence_score=HRV_COHERENCE_THRESHOLD,
            measured_at=datetime.now(UTC),
            source="simulated",
        )

    async def _append_audit_event(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        session_id: UUID,
        result: HRVGateResult,
    ) -> None:
        await db.execute(
            insert(AuditLog).values(
                tenant_id=tenant_id,
                actor_user_id=None,
                action="hrv_gate_evaluated",
                resource_type="session",
                resource_id=str(session_id),
                reason="hrv_gate_evaluated",
                metadata_json=result.model_dump(mode="json"),
                correlation_id=str(uuid4()),
            )
        )
