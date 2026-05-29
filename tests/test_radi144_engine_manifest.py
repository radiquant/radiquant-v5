"""Radi144 Engine Manifest Gate tests.

This gate validates Radi144's contract only. It must not add an engine domain
service, API route, result persistence implementation, or execution path.
"""

import json
from pathlib import Path

from fastapi.routing import APIRoute

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
RADI144_MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
WORKFLOW_MANIFEST = ROOT / "packages" / "contracts" / "workflows" / "workflow-manifest.v2.json"
EVENT_REGISTRY = ROOT / "packages" / "contracts" / "events" / "event-registry.v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_radi144_manifest_matches_workflow_first_vertical_slice() -> None:
    manifest = _load(RADI144_MANIFEST)
    workflow = _load(WORKFLOW_MANIFEST)

    assert manifest["module_id"] == "radi144"
    assert manifest["phase"] == "diagnose"
    assert set(manifest["workflow_bindings"]) == {"W-A", "W-B"}
    assert workflow["first_vertical_slice"]["module_id"] == "radi144"
    assert [substep["id"].replace("radi144.", "") for substep in manifest["substeps"]] == workflow["module_contracts"]["radi144"]["substeps"]


def test_radi144_manifest_keeps_execution_and_results_blocked() -> None:
    manifest = _load(RADI144_MANIFEST)
    runtime_scope = manifest["runtime_scope"]

    assert runtime_scope["engine_manifest_enabled"] is True
    assert runtime_scope["engine_domain_service_enabled"] is True
    assert runtime_scope["engine_execution_enabled"] is False
    assert runtime_scope["engine_api_enabled"] is False
    assert runtime_scope["result_persistence_enabled"] is False
    assert runtime_scope["client_projection_enabled"] is False

    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    forbidden_fragments = {"/engines", "/engine", "/modules", "/results", "/radi144"}
    allowed_radi144_paths = {
        "/engines/radi144/jobs",
        "/engines/radi144/jobs/{job_id}",
        "/engines/radi144/jobs/{job_id}/result",
    }
    assert not [path for path in runtime_paths for fragment in forbidden_fragments if fragment in path and path not in allowed_radi144_paths]


def test_radi144_result_contract_and_safety_are_privacy_preserving() -> None:
    manifest = _load(RADI144_MANIFEST)
    result_contract = manifest["result_contract"]
    safety = manifest["safety"]

    assert result_contract["raw_debug_allowed"] is False
    assert result_contract["client_projection_required"] is True
    assert result_contract["matrix_shape"] == [12, 12]
    assert result_contract["client_vector_dimensions"] == 256
    assert "provenance" in result_contract["required_fields"]
    assert safety["wellbeing_language_only"] is True
    assert safety["medical_claims_allowed"] is False
    assert safety["client_raw_debug_allowed"] is False
    assert safety["requires_active_analysis_consent"] is True


def test_radi144_manifest_events_are_registered() -> None:
    manifest = _load(RADI144_MANIFEST)
    registry = _load(EVENT_REGISTRY)
    event_types = {event_type for family in registry["families"] for event_type in family["events"]}

    assert set(manifest["events"]["required"]).issubset(event_types)
    assert manifest["events"]["failure_event"] == "module.radi144.failed"


def test_radi144_substeps_have_fallbacks_timeouts_and_no_unknown_refs() -> None:
    manifest = _load(RADI144_MANIFEST)
    input_ids = {item["id"] for item in manifest["inputs"]}
    output_ids = {item["id"] for item in manifest["outputs"]}

    for expected_order, substep in enumerate(manifest["substeps"], start=1):
        assert substep["order"] == expected_order
        assert substep["phase"] == "diagnose"
        assert substep["timeout_s"] > 0
        assert substep["fallback"]
        assert set(substep["input_refs"]).issubset(input_ids | output_ids)
        assert set(substep["output_refs"]).issubset(input_ids | output_ids)
