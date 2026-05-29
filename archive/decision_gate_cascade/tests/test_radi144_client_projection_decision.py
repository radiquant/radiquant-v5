"""Radi144 Client Projection Gate Decision tests.

The gate defines role projection boundaries only. It does not build projections,
open result APIs, persist results, enqueue workers, or execute Radi144.
"""

import json
from pathlib import Path

from fastapi.routing import APIRoute

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
RESULT_SCHEMA = ROOT / "packages" / "contracts" / "results" / "radi144-result.schema.v1.json"
PROJECTION_SCHEMA = ROOT / "packages" / "contracts" / "projections" / "radi144-client-projection.schema.v1.json"
PROJECTION_INSTANCE = ROOT / "packages" / "contracts" / "projections" / "radi144-client-projection.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_CLIENT_PROJECTION_GATE_DECISION.md"

FORBIDDEN_FIELDS = {
    "raw_resonance_matrix",
    "normalized_matrix",
    "client_vector",
    "raw_debug",
    "debug_json",
    "internal_state",
    "access_token",
    "password",
}


def test_projection_decision_records_boundary_without_enabling_builder() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    scope = manifest["runtime_scope"]

    assert scope["client_projection_boundary_decided"] is True
    assert scope["client_projection_enabled"] is False
    assert scope["result_persistence_enabled"] is False
    assert scope["engine_api_enabled"] is False
    assert scope["worker_jobs_enabled"] is False
    assert scope["engine_execution_enabled"] is False


def test_projection_schema_and_instance_are_linked() -> None:
    schema = json.loads(PROJECTION_SCHEMA.read_text(encoding="utf-8"))
    projection = json.loads(PROJECTION_INSTANCE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert schema["properties"]["schema_id"]["const"] == projection["schema_id"]
    assert manifest["client_projection_boundary"]["instance_path"] == "packages/contracts/projections/radi144-client-projection.v1.instance.json"
    assert projection["status"] == "boundary_decided_builder_not_opened"
    assert projection["builder_enabled"] is False
    assert projection["runtime_api_enabled"] is False


def test_role_projections_match_frontend_privacy_rules() -> None:
    projection = json.loads(PROJECTION_INSTANCE.read_text(encoding="utf-8"))

    assert projection["roles"]["client"]["projection"] == "calm_summary"
    assert projection["roles"]["therapist"]["projection"] == "professional_detail"
    assert FORBIDDEN_FIELDS.issubset(set(projection["forbidden_fields"]))
    for forbidden in ["raw_engine_output", "raw_resonance_matrix", "client_vector", "debug_json", "internal_state"]:
        assert forbidden in projection["roles"]["client"]["forbidden_sections"]


def test_projection_boundary_preserves_wellbeing_and_privacy_policy() -> None:
    projection = json.loads(PROJECTION_INSTANCE.read_text(encoding="utf-8"))

    assert projection["language_policy"]["wellbeing_language_only"] is True
    assert projection["language_policy"]["medical_claims_allowed"] is False
    assert projection["language_policy"]["healing_claims_allowed"] is False
    assert projection["privacy_policy"]["tenant_scoped"] is True
    assert projection["privacy_policy"]["purpose_required"] is True
    assert projection["privacy_policy"]["raw_debug_excluded"] is True


def test_result_schema_keeps_projection_placeholder_pending() -> None:
    result_schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))

    assert result_schema["properties"]["client_projection"]["properties"]["status"]["enum"] == ["pending_projection_builder"]
    assert result_schema["properties"]["client_projection"]["properties"]["raw_debug_excluded"]["const"] is True


def test_projection_decision_does_not_open_routes() -> None:
    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    forbidden_fragments = {"/engines", "/engine", "/modules", "/results", "/radi144", "/jobs"}
    allowed_radi144_paths = {
        "/engines/radi144/jobs",
        "/engines/radi144/jobs/{job_id}",
        "/engines/radi144/jobs/{job_id}/result",
    }

    assert not [path for path in runtime_paths for fragment in forbidden_fragments if fragment in path and path not in allowed_radi144_paths]


def test_project_anchor_and_decision_doc_advance_to_persistence_storage_decision() -> None:
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    assert "radi144_client_projection_gate_decision:" in project_text
    assert "status: boundary_decided_builder_not_opened" in project_text
    assert "radi144_result_persistence_storage_gate_decision" in project_text
    for blocker in ["client_projection_builder", "result_persistence", "engine_api_runtime_routes", "worker_jobs", "engine_execution"]:
        assert f"- {blocker}" in project_text
    for token in ["boundary-only", "client sees no raw/debug/internal data", "projection builder remains closed"]:
        assert token in decision_text
