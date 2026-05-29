"""Radi144 Engine Job Gate Decision tests.

The gate defines a contract-only job lifecycle and keeps runtime workers, API,
result persistence, projection builder, and engine execution closed.
"""

import json
from pathlib import Path
from uuid import uuid4

from fastapi.routing import APIRoute

import app.models  # noqa: F401 - register SQLAlchemy metadata
from app.db.base import Base
from app.main import app
from app.schemas.radi144_job import (
    Radi144EngineJobContract,
    Radi144JobFallbackPolicy,
    Radi144JobTimeoutPolicy,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
EVENTS = ROOT / "packages" / "contracts" / "events" / "event-registry.v1.json"
JOB_SCHEMA = ROOT / "packages" / "contracts" / "jobs" / "radi144-engine-job.schema.v1.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_ENGINE_JOB_GATE_DECISION.md"

RUNTIME_JOB_TABLES = {"engine_jobs", "module_jobs"}
CORE_STORAGE_TABLES = {"module_runs", "module_results", "module_provenances"}
DEFERRED_STORAGE_TABLES = {"module_inputs", "module_outputs"}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _job_contract() -> Radi144EngineJobContract:
    manifest = _manifest()
    return Radi144EngineJobContract(
        job_id=uuid4(),
        tenant_id=uuid4(),
        session_id=uuid4(),
        workflow_run_id=uuid4(),
        workflow_step_run_id=uuid4(),
        status="queued",
        allowed_events=manifest["job_contract"]["required_events"],
        timeout_policy=Radi144JobTimeoutPolicy(max_total_timeout_s=manifest["job_contract"]["max_total_timeout_s"]),
        fallback_policy=Radi144JobFallbackPolicy(),
    )


def test_job_decision_enables_contract_only_scope() -> None:
    manifest = _manifest()
    scope = manifest["runtime_scope"]

    assert scope["engine_job_contract_enabled"] is True
    assert scope["worker_jobs_enabled"] is False
    assert scope["engine_execution_enabled"] is False
    assert scope["engine_api_enabled"] is False
    assert scope["result_persistence_enabled"] is False
    assert scope["client_projection_enabled"] is False


def test_job_schema_is_linked_from_manifest() -> None:
    manifest = _manifest()
    schema = json.loads(JOB_SCHEMA.read_text(encoding="utf-8"))

    assert manifest["job_contract"]["schema_path"] == "packages/contracts/jobs/radi144-engine-job.schema.v1.json"
    assert manifest["job_contract"]["schema_id"] == schema["properties"]["schema_id"]["const"]
    assert schema["properties"]["worker_runtime_enabled"]["const"] is False
    assert schema["properties"]["engine_execution_enabled"]["const"] is False


def test_job_events_are_registered_and_timeout_matches_substeps() -> None:
    manifest = _manifest()
    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    event_types = {event for family in events["families"] for event in family["events"]}
    timeout_total = sum(int(substep["timeout_s"]) for substep in manifest["substeps"])

    assert set(manifest["job_contract"]["required_events"]).issubset(event_types)
    assert manifest["job_contract"]["max_total_timeout_s"] == timeout_total
    assert events["runtime_scope"]["job_tracker_enabled"] is False


def test_job_contract_dto_cannot_enable_runtime_execution() -> None:
    contract = _job_contract()

    assert contract.schema_id == "radi144_engine_job_v1"
    assert contract.job_kind == "engine_module_contract_only"
    assert contract.worker_runtime_enabled is False
    assert contract.engine_execution_enabled is False
    assert contract.api_exposure == "blocked_until_engine_api_gate"
    assert contract.result_persistence == "blocked_until_result_persistence_gate"
    assert contract.client_projection == "blocked_until_client_projection_gate"


def test_job_decision_does_not_open_runtime_job_tables_routes_or_workers() -> None:
    metadata_tables = set(Base.metadata.tables)
    assert not ((RUNTIME_JOB_TABLES | DEFERRED_STORAGE_TABLES) & metadata_tables)
    if "radi144_result_persistence_storage_gate_decision" in PROJECT_ANCHOR.read_text(encoding="utf-8"):
        assert CORE_STORAGE_TABLES.issubset(metadata_tables)
    else:
        assert not (CORE_STORAGE_TABLES & metadata_tables)

    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    forbidden_fragments = {"/engines", "/engine", "/modules", "/results", "/radi144", "/jobs"}
    allowed_radi144_paths = {
        "/engines/radi144/jobs",
        "/engines/radi144/jobs/{job_id}",
        "/engines/radi144/jobs/{job_id}/result",
    }
    assert not [path for path in runtime_paths for fragment in forbidden_fragments if fragment in path and path not in allowed_radi144_paths]

    route_gate_opened = "radi144_engine_api_runtime_route_gate_decision" in PROJECT_ANCHOR.read_text(encoding="utf-8")
    forbidden_runtime_files = ["apps/api/app/workers/radi144.py", "apps/api/app/jobs/radi144.py"]
    if not route_gate_opened:
        forbidden_runtime_files.extend(["apps/api/app/routes/radi144.py", "apps/api/app/routes/engines.py"])
    for rel in forbidden_runtime_files:
        assert not (ROOT / rel).exists()


def test_project_anchor_and_decision_doc_record_next_gate() -> None:
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    assert "radi144_engine_job_gate_decision:" in project_text
    assert "status: initialized_contract_only_job_lifecycle" in project_text
    assert "radi144_engine_api_gate_decision" in project_text
    for blocker in ["worker_jobs", "engine_execution", "engine_api", "result_persistence", "client_projection_builder"]:
        assert f"- {blocker}" in project_text
        assert blocker in decision_text
