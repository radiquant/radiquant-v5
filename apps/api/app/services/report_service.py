"""Tenant-scoped report generation from materialized projections."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.engine import ModuleProjection, ModuleRun
from app.schemas.report import ClientReport, TherapistAppendix
from app.services.claim_linter import ClaimLinterService
from app.services.synergy_service import SynergyService

TECHNICAL_REPORT_KEYS = {
    "access_token",
    "compute_backend",
    "cpu_execution_enabled",
    "debug_json",
    "gpu_cuda_execution_enabled",
    "internal_state",
    "module_run_id",
    "password",
    "projection_written",
    "raw_debug",
    "result_payload_json",
    "worker_outcome",
}


class ReportService:
    """Build client-safe and therapist report projections."""

    async def build_client_report(
        self,
        session_id: UUID,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> ClientReport:
        return await self._build_report(
            session_id=session_id,
            tenant_id=tenant_id,
            role="client",
            db=db,
        )

    async def build_therapist_appendix(
        self,
        session_id: UUID,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> TherapistAppendix:
        report = await self._build_report(
            session_id=session_id,
            tenant_id=tenant_id,
            role="therapist",
            db=db,
        )
        synergy = await SynergyService().compute(
            session_id=session_id,
            tenant_id=tenant_id,
            db=db,
        )
        return TherapistAppendix(
            session_id=report.session_id,
            tenant_id=report.tenant_id,
            role="therapist",
            summary=report.summary,
            modules=report.modules,
            generated_at=report.generated_at,
            synergy=synergy,
        )

    async def _build_report(
        self,
        *,
        session_id: UUID,
        tenant_id: UUID,
        role: Literal["client", "therapist"],
        db: AsyncSession,
    ) -> ClientReport:
        rows = list(
            (
                await db.execute(
                    select(ModuleRun.module_id, ModuleProjection.projection_json)
                    .join(ModuleProjection, ModuleProjection.module_run_id == ModuleRun.id)
                    .where(
                        ModuleRun.tenant_id == tenant_id,
                        ModuleRun.session_id == session_id,
                        ModuleProjection.tenant_id == tenant_id,
                        ModuleProjection.role == role,
                    )
                    .order_by(ModuleRun.module_id)
                )
            ).all()
        )
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No report projections found for session",
            )

        modules: list[str] = []
        fragments: list[str] = []
        for module_id, payload in rows:
            module = str(module_id)
            modules.append(module)
            safe_payload = self._filter_payload(payload)
            fragments.append(self._summary_fragment(module, safe_payload))

        summary = " ".join(fragments)
        ClaimLinterService().lint(summary)
        return ClientReport(
            session_id=session_id,
            tenant_id=tenant_id,
            role=role,
            summary=summary,
            modules=modules,
            generated_at=datetime.now(UTC),
        )

    def _filter_payload(self, payload: object) -> object:
        if isinstance(payload, dict):
            return {
                key: self._filter_payload(value)
                for key, value in payload.items()
                if key not in TECHNICAL_REPORT_KEYS
            }
        if isinstance(payload, list):
            return [self._filter_payload(item) for item in payload]
        return payload

    def _summary_fragment(self, module: str, payload: object) -> str:
        values = self._text_values(payload)
        if not values:
            return f"{module}: client-safe projection available."
        return f"{module}: {'; '.join(values[:3])}."

    def _text_values(self, payload: object) -> list[str]:
        if isinstance(payload, dict):
            values: list[str] = []
            for value in payload.values():
                values.extend(self._text_values(value))
            return values
        if isinstance(payload, list):
            values = []
            for item in payload:
                values.extend(self._text_values(item))
            return values
        if isinstance(payload, str) and payload:
            return [payload]
        if isinstance(payload, int | float | bool):
            return [str(payload)]
        return []
