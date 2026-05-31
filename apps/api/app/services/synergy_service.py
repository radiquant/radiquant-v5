"""Tenant-scoped cross-module synergy synthesis."""

from __future__ import annotations

from itertools import combinations
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.engine import ModuleResult, ModuleRun
from app.schemas.synergy import SynergyConflict, SynergyResult

EXPECTED_MODULES = (
    "radi144",
    "radiworks",
    "radimorphic",
    "radiblohm",
    "radithoms",
    "radicopen",
)


class SynergyService:
    """Compute public-safe session synthesis from tenant-scoped module results."""

    async def compute(
        self,
        *,
        session_id: UUID,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> SynergyResult:
        """Compute cross-module synthesis for a tenant-owned session."""
        rows = list(
            (
                await db.execute(
                    select(ModuleRun.module_id, ModuleResult.result_payload_json)
                    .join(ModuleRun, ModuleRun.id == ModuleResult.module_run_id)
                    .where(
                        ModuleResult.tenant_id == tenant_id,
                        ModuleRun.tenant_id == tenant_id,
                        ModuleRun.session_id == session_id,
                    )
                    .order_by(ModuleRun.module_id)
                )
            ).all()
        )
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No module results found for session",
            )

        complete_set = {str(module_id) for module_id, _payload in rows}
        all_modules = [module for module in EXPECTED_MODULES if module not in complete_set]
        extra_modules = sorted(module for module in complete_set if module not in EXPECTED_MODULES)
        modules_complete = [
            module for module in EXPECTED_MODULES if module in complete_set
        ] + extra_modules
        modules_pending = all_modules
        total_modules = len(modules_complete) + len(modules_pending)
        confidence = len(modules_complete) / max(total_modules, 1)
        conflicts = self._detect_conflicts(
            [(str(module_id), payload) for module_id, payload in rows]
        )
        summary = self._summary(
            complete_count=len(modules_complete),
            total_count=total_modules,
            conflict_count=len(conflicts),
        )
        return SynergyResult(
            session_id=session_id,
            tenant_id=tenant_id,
            confidence=confidence,
            modules_complete=modules_complete,
            modules_pending=modules_pending,
            conflicts=conflicts,
            consensus_summary=summary,
        )

    def _detect_conflicts(
        self,
        rows: list[tuple[str, dict[str, object]]],
    ) -> list[SynergyConflict]:
        scored = [
            (module_id, score)
            for module_id, payload in rows
            if (score := self._score(payload)) is not None
        ]
        conflicts: list[SynergyConflict] = []
        for (module_a, score_a), (module_b, score_b) in combinations(scored, 2):
            difference = abs(score_a - score_b)
            if difference <= 0.7:
                continue
            severity: str = "high" if round(difference, 4) >= 0.9 else "medium"
            conflicts.append(
                SynergyConflict(
                    module_a=module_a,
                    module_b=module_b,
                    conflict_type="score_polarity",
                    severity=severity,  # type: ignore[arg-type]
                )
            )
        return conflicts

    def _score(self, payload: dict[str, object]) -> float | None:
        score = payload.get("score")
        if isinstance(score, int | float):
            return float(score)
        return None

    def _summary(self, *, complete_count: int, total_count: int, conflict_count: int) -> str:
        if conflict_count:
            return (
                f"Completed {complete_count} of {total_count} modules; "
                f"{conflict_count} cross-module conflict(s) require review."
            )
        return f"Completed {complete_count} of {total_count} modules with no conflicts detected."
