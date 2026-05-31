"""RadiMorphic result writer."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.engine import ModuleRun
from app.models.radimorphic import RadiMorphicResult
from app.schemas.radimorphic import RadiMorphicResultPayload

FORBIDDEN_RESULT_KEYS = {
    "raw_debug",
    "debug_json",
    "internal_state",
    "access_token",
    "password",
}


class RadiMorphicResultWriteError(ValueError):
    """Raised when a RadiMorphic result cannot be persisted safely."""

    public_detail = "RadiMorphic result write rejected"

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


class RadiMorphicResultWriter:
    """Persist validated RadiMorphic result DTOs with tenant guards."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def persist_result(self, *, result: RadiMorphicResultPayload) -> ModuleRun:
        """Persist a RadiMorphic result idempotently without committing."""
        payload = result.model_dump(mode="json")
        forbidden_key = _find_forbidden_key(payload)
        if forbidden_key is not None:
            raise RadiMorphicResultWriteError(f"forbidden_result_key:{forbidden_key}")

        module_run = await self.session.scalar(
            select(ModuleRun).where(
                ModuleRun.id == result.module_run_id,
                ModuleRun.tenant_id == result.tenant_id,
                ModuleRun.module_id == "radimorphic",
            )
        )
        if module_run is None:
            raise RadiMorphicResultWriteError("module_run_not_found_for_tenant")

        existing = await self.session.scalar(
            select(RadiMorphicResult).where(
                RadiMorphicResult.tenant_id == result.tenant_id,
                RadiMorphicResult.module_run_id == result.module_run_id,
            )
        )
        if existing is not None:
            module_run.status = "result_stored"
            await self.session.flush()
            return module_run

        module_run.status = "result_stored"
        module_run.schema_id = result.schema_id
        module_run.job_contract_schema_id = "radimorphic_engine_job_v1"
        self.session.add(
            RadiMorphicResult(
                tenant_id=result.tenant_id,
                module_run_id=result.module_run_id,
                schema_id=result.schema_id,
                result_payload_json=payload,
                projection_status=result.projection_status,
            )
        )
        await self.session.flush()
        return module_run

    async def get_result(
        self,
        *,
        tenant_id: UUID,
        module_run_id: UUID,
    ) -> RadiMorphicResult | None:
        """Return a tenant-scoped RadiMorphic result by module run id."""
        return await self.session.scalar(
            select(RadiMorphicResult).where(
                RadiMorphicResult.tenant_id == tenant_id,
                RadiMorphicResult.module_run_id == module_run_id,
            )
        )
