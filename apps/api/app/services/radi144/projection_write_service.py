"""Radi144 projection write service (ADR-0002).

Projection Write Service scope: idempotently materialize per-role projections
into module_projections for an already persisted ModuleResult. This service
does not execute engines, expose API routes, or modify existing projection rows.
"""

from __future__ import annotations

import dataclasses
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.engine import ModuleProjection, ModuleResult
from app.schemas.radi144_result import Radi144Result
from app.services.radi144.projection_builder import (
    Radi144ProjectionBuilder,
    Radi144ProjectionError,
)

_PROJECTION_ROLES: tuple[str, str] = ("client", "therapist")


class ProjectionWriteError(ValueError):
    """Raised when a projection cannot be safely materialized."""

    public_detail = "Projection write rejected"

    def __init__(self, reason: str) -> None:
        super().__init__(self.public_detail)
        self.reason = reason


@dataclasses.dataclass(frozen=True, slots=True)
class ProjectionWriteResult:
    """Summary of the materialization run."""

    module_run_id: UUID
    tenant_id: UUID
    written: int
    skipped: int


class ProjectionWriteService:
    """Idempotently materialize Radi144 projections into module_projections."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._builder = Radi144ProjectionBuilder()

    async def persist_projection(
        self, *, module_run_id: UUID, tenant_id: UUID
    ) -> ProjectionWriteResult:
        """Materialize client and therapist projections for a stored result.

        Idempotent: existing (tenant_id, module_run_id, role) rows are skipped.
        The caller is responsible for committing.
        """
        module_result = await self._session.scalar(
            select(ModuleResult).where(
                ModuleResult.module_run_id == module_run_id,
                ModuleResult.tenant_id == tenant_id,
            )
        )
        if module_result is None:
            raise ProjectionWriteError("module_result_not_found_for_tenant")

        try:
            result = Radi144Result.model_validate(module_result.result_payload_json)
        except Exception as exc:
            raise ProjectionWriteError(f"result_payload_invalid:{exc}") from exc

        written = 0
        skipped = 0
        for role in _PROJECTION_ROLES:
            existing = await self._session.scalar(
                select(ModuleProjection.id).where(
                    ModuleProjection.tenant_id == tenant_id,
                    ModuleProjection.module_run_id == module_run_id,
                    ModuleProjection.role == role,
                )
            )
            if existing is not None:
                skipped += 1
                continue

            try:
                projection = self._builder.build_projection(result=result, role=role)  # type: ignore[arg-type]
            except Radi144ProjectionError as exc:
                raise ProjectionWriteError(f"projection_build_failed:{exc.reason}") from exc

            self._session.add(
                ModuleProjection(
                    tenant_id=tenant_id,
                    module_run_id=module_run_id,
                    role=role,
                    projection_kind=projection.projection,
                    projection_json=projection.model_dump(mode="json"),
                    raw_debug_excluded=True,
                )
            )
            written += 1

        await self._session.flush()
        return ProjectionWriteResult(
            module_run_id=module_run_id,
            tenant_id=tenant_id,
            written=written,
            skipped=skipped,
        )
