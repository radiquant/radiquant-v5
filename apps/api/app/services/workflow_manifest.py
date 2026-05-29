"""Workflow manifest access for the Workflow API Gate.

The service is read-only and may only plan steps that are explicitly present in
packages/contracts/workflows/workflow-manifest.v2.json.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.models.client import ConsentPurpose

ROOT = Path(__file__).resolve().parents[4]
MANIFEST_PATH = ROOT / "packages" / "contracts" / "workflows" / "workflow-manifest.v2.json"


class WorkflowManifestError(Exception):
    """Base class for safe workflow manifest planning failures."""

    public_detail = "Workflow cannot be planned"


class UnknownWorkflowError(WorkflowManifestError):
    """Raised when a workflow is not present in the manifest."""

    public_detail = "Workflow not found"


class WorkflowNotPlannableError(WorkflowManifestError):
    """Raised when a workflow still needs a later configuration or feature gate."""

    public_detail = "Workflow requires a later gate"


@dataclass(frozen=True)
class WorkflowStepPlan:
    """One manifest-derived workflow step."""

    step_index: int
    module_id: str
    phase: str


@dataclass(frozen=True)
class WorkflowPlan:
    """Manifest-derived workflow plan without execution data."""

    workflow_id: str
    workflow_slug: str
    required_consent_purposes: tuple[ConsentPurpose, ...]
    steps: tuple[WorkflowStepPlan, ...]


@lru_cache(maxsize=1)
def _load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


class WorkflowManifestService:
    """Build safe workflow plans from the committed manifest."""

    def __init__(self, manifest: dict[str, Any] | None = None) -> None:
        self.manifest = manifest if manifest is not None else _load_manifest()

    def build_plan(self, workflow_id: str) -> WorkflowPlan:
        workflows = {workflow.get("id"): workflow for workflow in self.manifest.get("workflows", [])}
        workflow = workflows.get(workflow_id)
        if not isinstance(workflow, dict) or workflow.get("status") != "confirmed":
            raise UnknownWorkflowError
        if workflow.get("feature_flag_required") is True:
            raise WorkflowNotPlannableError

        module_order = workflow.get("module_order")
        if not isinstance(module_order, list) or not all(isinstance(module_id, str) for module_id in module_order):
            raise WorkflowNotPlannableError

        module_phases = {
            module.get("id"): module.get("phase")
            for module in self.manifest.get("modules", [])
            if isinstance(module, dict) and isinstance(module.get("id"), str)
        }
        steps: list[WorkflowStepPlan] = []
        for step_index, module_id in enumerate(module_order):
            phase = module_phases.get(module_id)
            if not isinstance(phase, str):
                raise WorkflowNotPlannableError
            steps.append(WorkflowStepPlan(step_index=step_index, module_id=module_id, phase=phase))

        consent_purposes: list[ConsentPurpose] = []
        for raw_purpose in workflow.get("required_consent_purposes", []):
            try:
                consent_purposes.append(ConsentPurpose(raw_purpose))
            except ValueError as exc:
                raise WorkflowNotPlannableError from exc

        return WorkflowPlan(
            workflow_id=workflow_id,
            workflow_slug=str(workflow["slug"]),
            required_consent_purposes=tuple(consent_purposes),
            steps=tuple(steps),
        )
