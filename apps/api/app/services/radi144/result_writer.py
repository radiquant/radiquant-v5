"""Radi144 runtime result write service.

Runtime Result Write Gate scope: persist an already validated Radi144Result into
tenant-scoped ModuleRun/ModuleResult/ModuleProvenance storage. This service is
not wired to API routes, workers, projection builders, or engine execution.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.engine import ModuleProvenance, ModuleResult, ModuleRun
from app.models.workflow import WorkflowStepRun
from app.schemas.radi144_result import Radi144Result

FORBIDDEN_RESULT_KEYS = {
    "raw_debug",
    "debug_json",
    "internal_state",
    "access_token",
    "password",
}


class Radi144ResultWriteError(ValueError):
    """Raised when a Radi144 result cannot be persisted safely."""

    public_detail = "Radi144 result write rejected"

    def __init__(self, reason: str) -> None:
        super().__init__(self.public_detail)
        self.reason = reason


def _find_forbidden_key(value: object) -> str | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FORBIDDEN_RESULT_KEYS:
                return key
            found = _find_forbidden_key(nested)
            if found is not None:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _find_forbidden_key(nested)
            if found is not None:
                return found
    return None


class Radi144ResultWriter:
    """Persist validated Radi144 result DTOs with tenant and projection guards."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def persist_result(self, *, result: Radi144Result, workflow_step_run_id: UUID) -> ModuleRun:
        """Persist a Radi144 result without committing the transaction."""
        payload = result.model_dump(mode="json")
        forbidden_key = _find_forbidden_key(payload)
        if forbidden_key is not None:
            raise Radi144ResultWriteError(f"forbidden_result_key:{forbidden_key}")
        if result.retention.raw_debug_allowed is not False:
            raise Radi144ResultWriteError("raw_debug_must_remain_forbidden")
        if result.retention.client_projection_required is not True:
            raise Radi144ResultWriteError("client_projection_required")
        if result.client_projection.status != "pending_projection_builder":
            raise Radi144ResultWriteError("projection_builder_must_remain_pending")

        workflow_step = await self.session.scalar(
            select(WorkflowStepRun).where(
                WorkflowStepRun.id == workflow_step_run_id,
                WorkflowStepRun.tenant_id == result.tenant_id,
                WorkflowStepRun.workflow_run_id == result.workflow_run_id,
                WorkflowStepRun.module_id == "radi144",
            )
        )
        if workflow_step is None:
            raise Radi144ResultWriteError("workflow_step_not_found_for_tenant")

        existing = await self.session.scalar(
            select(ModuleRun).where(ModuleRun.id == result.module_run_id, ModuleRun.tenant_id == result.tenant_id)
        )
        if existing is not None:
            if (
                existing.workflow_step_run_id != workflow_step_run_id
                or existing.workflow_run_id != result.workflow_run_id
                or existing.session_id != result.session_id
                or existing.module_id != "radi144"
                or existing.status != "queued"
            ):
                raise Radi144ResultWriteError("module_run_already_persisted")
            result_exists = await self.session.scalar(select(ModuleResult.id).where(ModuleResult.module_run_id == existing.id))
            if result_exists is not None:
                raise Radi144ResultWriteError("module_run_already_persisted")
            existing.status = "result_stored"
            existing.schema_id = result.schema_id
            existing.job_contract_schema_id = "radi144_engine_job_v1"
            module_run = existing
        else:
            module_run = ModuleRun(
                id=result.module_run_id,
                tenant_id=result.tenant_id,
                session_id=result.session_id,
                workflow_run_id=result.workflow_run_id,
                workflow_step_run_id=workflow_step_run_id,
                module_id="radi144",
                phase="diagnose",
                status="result_stored",
                schema_id=result.schema_id,
                job_contract_schema_id="radi144_engine_job_v1",
            )
        module_result = ModuleResult(
            tenant_id=result.tenant_id,
            module_run_id=result.module_run_id,
            schema_id=result.schema_id,
            result_payload_json=payload,
            retention_json=result.retention.model_dump(mode="json"),
            projection_status=result.client_projection.status,
            raw_debug_allowed=result.retention.raw_debug_allowed,
            client_projection_required=result.retention.client_projection_required,
        )
        module_provenance = ModuleProvenance(
            tenant_id=result.tenant_id,
            module_run_id=result.module_run_id,
            algorithm_version=result.provenance.algorithm_version,
            manifest_version=result.provenance.manifest_version,
            input_hash=result.provenance.input_hash,
            reference_matrix_version=result.provenance.reference_matrix_version,
            compute_backend=result.provenance.compute_backend,
            duration_ms=result.provenance.duration_ms,
            provenance_json=result.provenance.model_dump(mode="json"),
        )
        self.session.add_all([module_run, module_result, module_provenance])
        await self.session.flush()
        return module_run
