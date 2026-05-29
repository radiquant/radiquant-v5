#!/usr/bin/env python3
"""Validate the Radi144 Engine Job Gate Decision.

This gate opens only a contract-level job lifecycle descriptor. It does not
create runtime workers, queues, API routes, persistence, projections, or engine
execution.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import uuid4

from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

import app.models  # noqa: F401,E402 - register ORM metadata
from app.db.base import Base  # noqa: E402
from app.main import app  # noqa: E402
from app.schemas.radi144_job import (  # noqa: E402
    Radi144EngineJobContract,
    Radi144JobFallbackPolicy,
    Radi144JobTimeoutPolicy,
)

MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
EVENTS = ROOT / "packages" / "contracts" / "events" / "event-registry.v1.json"
JOB_SCHEMA = ROOT / "packages" / "contracts" / "jobs" / "radi144-engine-job.schema.v1.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_ENGINE_JOB_GATE_DECISION.md"

RUNTIME_JOB_TABLES = {"engine_jobs", "module_jobs"}
CORE_STORAGE_TABLES = {"module_runs", "module_results", "module_provenances"}
DEFERRED_STORAGE_TABLES = {"module_inputs", "module_outputs"}
ALLOWED_RADI144_RUNTIME_PATHS = {
    "/engines/radi144/jobs",
    "/engines/radi144/jobs/{job_id}",
    "/engines/radi144/jobs/{job_id}/result",
}
FORBIDDEN_ROUTE_FRAGMENTS = {"/engines", "/engine", "/modules", "/results", "/radi144", "/jobs"}
FORBIDDEN_RUNTIME_PATHS = [
    ROOT / "apps" / "api" / "app" / "workers" / "radi144.py",
    ROOT / "apps" / "api" / "app" / "jobs" / "radi144.py",
    ROOT / "apps" / "api" / "app" / "routes" / "radi144.py",
    ROOT / "apps" / "api" / "app" / "routes" / "engines.py",
]
REQUIRED_BLOCKERS = {
    "worker_jobs",
    "engine_execution",
    "engine_api",
    "result_persistence",
    "client_projection_builder",
}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    event_registry = json.loads(EVENTS.read_text(encoding="utf-8"))
    job_schema = json.loads(JOB_SCHEMA.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("engine_job_contract_enabled") is not True:
        fail("Radi144 job contract must be enabled")
    for blocked_flag in ["worker_jobs_enabled", "engine_execution_enabled", "engine_api_enabled", "result_persistence_enabled", "client_projection_enabled"]:
        if runtime_scope.get(blocked_flag) is not False:
            fail(f"{blocked_flag} must remain false")

    job_contract = manifest.get("job_contract", {})
    if job_contract.get("schema_path") != "packages/contracts/jobs/radi144-engine-job.schema.v1.json":
        fail("Radi144 manifest must link the job schema")
    if job_schema.get("properties", {}).get("schema_id", {}).get("const") != job_contract.get("schema_id"):
        fail("Radi144 job schema_id drift")
    if job_contract.get("worker_runtime_enabled") is not False or job_contract.get("engine_execution_enabled") is not False:
        fail("Radi144 job contract must remain contract-only")

    event_types = {event for family in event_registry.get("families", []) for event in family.get("events", [])}
    missing_events = sorted(set(job_contract.get("required_events", [])) - event_types)
    if missing_events:
        fail(f"Radi144 job contract references unknown events: {missing_events}")
    if event_registry.get("runtime_scope", {}).get("job_tracker_enabled") is not False:
        fail("Runtime JobTracker must remain disabled for the decision gate")

    substep_timeout_total = sum(int(substep["timeout_s"]) for substep in manifest.get("substeps", []))
    if job_contract.get("max_total_timeout_s") != substep_timeout_total:
        fail("Radi144 job timeout must equal manifest substep timeout total")

    sample = Radi144EngineJobContract(
        job_id=uuid4(),
        tenant_id=uuid4(),
        session_id=uuid4(),
        workflow_run_id=uuid4(),
        workflow_step_run_id=uuid4(),
        status="queued",
        allowed_events=job_contract["required_events"],
        timeout_policy=Radi144JobTimeoutPolicy(max_total_timeout_s=substep_timeout_total),
        fallback_policy=Radi144JobFallbackPolicy(),
    )
    if sample.worker_runtime_enabled is not False or sample.engine_execution_enabled is not False:
        fail("Radi144 job DTO enabled runtime execution unexpectedly")

    metadata_tables = set(Base.metadata.tables)
    opened_runtime_tables = sorted((RUNTIME_JOB_TABLES | DEFERRED_STORAGE_TABLES) & metadata_tables)
    if opened_runtime_tables:
        fail(f"Engine job/input-output tables opened too early: {opened_runtime_tables}")
    if "radi144_result_persistence_storage_gate_decision" in project_text:
        missing_storage_tables = sorted(CORE_STORAGE_TABLES - metadata_tables)
        if missing_storage_tables:
            fail(f"Storage gate opened but core storage tables are missing: {missing_storage_tables}")
    else:
        opened_storage_tables = sorted(CORE_STORAGE_TABLES & metadata_tables)
        if opened_storage_tables:
            fail(f"Engine storage tables opened before storage gate: {opened_storage_tables}")

    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    allowed_paths = ALLOWED_RADI144_RUNTIME_PATHS if "radi144_engine_api_runtime_route_gate_decision" in project_text else set()
    forbidden_routes = sorted(path for path in runtime_paths for fragment in FORBIDDEN_ROUTE_FRAGMENTS if fragment in path and path not in allowed_paths)
    if forbidden_routes:
        fail(f"Engine/job/result routes opened too early: {forbidden_routes}")

    route_gate_opened = "radi144_engine_api_runtime_route_gate_decision" in project_text
    runtime_path_candidates = FORBIDDEN_RUNTIME_PATHS if not route_gate_opened else FORBIDDEN_RUNTIME_PATHS[:2]
    existing_runtime_paths = [str(path.relative_to(ROOT)) for path in runtime_path_candidates if path.exists()]
    if existing_runtime_paths:
        fail(f"Radi144 runtime worker/API files opened too early: {existing_runtime_paths}")

    for token in ["radi144_engine_job_gate_decision", "status: initialized_contract_only_job_lifecycle", "radi144_engine_api_gate_decision"]:
        if token not in project_text:
            fail(f"Project anchor missing job decision token: {token}")
    for blocker in REQUIRED_BLOCKERS:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["contract-only", "worker_jobs", "engine_execution", "radi144_engine_api_gate_decision"]:
        if token not in decision_text:
            fail(f"Decision doc missing token: {token}")

    print("[OK] Radi144 engine job lifecycle is contract-only")
    print("[OK] Job events and timeout policy align with manifest/event registry")
    print("[OK] Worker jobs, engine API, persistence, projections, and execution remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
