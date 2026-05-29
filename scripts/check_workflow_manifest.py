#!/usr/bin/env python3
"""Strict workflow manifest and Workflow API Gate validation for radiquant-v5.

The Workflow API Gate may plan manifest-derived workflow runs. Realtime replay
is available after its gate; Workflow UI controls and engine execution remain disabled.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "contracts" / "workflows" / "workflow-manifest.v2.json"

REQUIRED_WORKFLOWS = ["W-A", "W-B", "W-C", "W-D", "W-E", "W-F", "W-L"]
REQUIRED_MODULES = ["radi144", "radiworks", "radimorphic", "radiblohm", "radithoms", "radicopen"]
REQUIRED_PHASES = {"diagnose", "analyse", "harmonize", "reflect"}
W_B_ORDER = REQUIRED_MODULES
FORBIDDEN_RUNTIME_FLAGS = ["workflow_ui_enabled", "engine_execution_enabled"]
REQUIRED_ANTI_DRIFT = {
    "no_workflow_api_before_manifest_gate",
    "no_workflow_ui_without_manifest_step",
    "no_progress_without_event_or_explicit_fallback",
    "no_engine_execution_without_module_contract",
}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_manifest() -> dict[str, Any]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail("Workflow manifest must be a JSON object")
    return data


def main() -> int:
    manifest = load_manifest()

    runtime_scope = manifest.get("runtime_scope", {})
    require(isinstance(runtime_scope, dict), "runtime_scope must be an object")
    require(runtime_scope.get("workflow_api_enabled") is True, "workflow_api_enabled must be true after Workflow API Gate")
    for flag in FORBIDDEN_RUNTIME_FLAGS:
        require(runtime_scope.get(flag) is False, f"{flag} must remain false after Workflow API Gate")
    require(
        runtime_scope.get("realtime_required_but_not_enabled_until_fallback_gate") is False,
        "Realtime fallback gate has opened; manifest flag must reflect that",
    )

    phases = {phase.get("id") for phase in manifest.get("phases", []) if isinstance(phase, dict)}
    require(REQUIRED_PHASES.issubset(phases), f"Missing required phases: {sorted(REQUIRED_PHASES - phases)}")

    workflows = {workflow.get("id"): workflow for workflow in manifest.get("workflows", []) if isinstance(workflow, dict)}
    for workflow_id in REQUIRED_WORKFLOWS:
        require(workflow_id in workflows, f"Missing workflow {workflow_id}")
        workflow = workflows[workflow_id]
        require(workflow.get("status") == "confirmed", f"Workflow {workflow_id} must be confirmed")
        require(bool(workflow.get("required_consent_purposes")), f"Workflow {workflow_id} lacks consent purposes")
        phase_sequence = workflow.get("phase_sequence", [])
        require(isinstance(phase_sequence, list) and bool(phase_sequence), f"Workflow {workflow_id} lacks phase_sequence")
        require(set(phase_sequence).issubset(REQUIRED_PHASES), f"Workflow {workflow_id} has invalid phase")
        if workflow.get("realtime_required") is True:
            require(workflow.get("fallback_required") is True, f"Workflow {workflow_id} requires realtime without fallback")

    require(workflows["W-B"].get("module_order") == W_B_ORDER, "W-B must use canonical six-module order")
    require(workflows["W-E"].get("approval_required") is True, "W-E harmonization must require approval")
    require(workflows["W-L"].get("feature_flag_required") is True, "W-L Labs must be feature-flagged")

    modules = {module.get("id"): module for module in manifest.get("modules", []) if isinstance(module, dict)}
    for module_id in REQUIRED_MODULES:
        require(module_id in modules, f"Missing module {module_id}")
        require(modules[module_id].get("phase") in REQUIRED_PHASES, f"Module {module_id} has invalid phase")

    module_contracts = manifest.get("module_contracts", {})
    require(isinstance(module_contracts, dict), "module_contracts must be object")
    for module_id in REQUIRED_MODULES:
        contract = module_contracts.get(module_id)
        require(isinstance(contract, dict), f"Missing module contract {module_id}")
        require(contract.get("phase") == modules[module_id].get("phase"), f"Module contract phase drift: {module_id}")
        require("consent_purpose_gate" in contract.get("required_pre_gates", []), f"Module {module_id} lacks consent gate")
        require("final_audit" in contract.get("required_post_gates", []), f"Module {module_id} lacks final audit gate")
        substeps = contract.get("substeps", [])
        require(isinstance(substeps, list) and len(substeps) >= 8, f"Module {module_id} needs at least 8 substeps")

    first = manifest.get("first_vertical_slice", {})
    require(first.get("module_id") == "radi144", "First vertical slice must remain Radi144")
    require(set(first.get("workflow_ids", [])) == {"W-A", "W-B"}, "Radi144 first slice must be tied to W-A and W-B")
    require(first.get("required_substeps") == module_contracts["radi144"].get("substeps"), "Radi144 first slice substeps drift")

    anti_drift = set(manifest.get("anti_drift_rules", []))
    require(REQUIRED_ANTI_DRIFT.issubset(anti_drift), "Workflow anti-drift rules incomplete")

    print(f"[OK] workflow manifest workflows validated: {', '.join(REQUIRED_WORKFLOWS)}")
    print(f"[OK] workflow manifest modules validated: {', '.join(REQUIRED_MODULES)}")
    print("[OK] workflow API enabled for manifest-derived planning only; workflow UI and engine execution remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
