#!/usr/bin/env python3
"""Validate the Radi144 Worker Job Gate Decision.

This gate opens tenant-scoped API job records (ModuleRun rows) only. It does
not start worker runtimes, write results from the job route, build projections
from the create route, or execute Radi144.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

import app.models  # noqa: F401,E402 - register ORM metadata
from app.db.base import Base  # noqa: E402
from app.main import app  # noqa: E402

MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
JOB_RECORD_SCHEMA = ROOT / "packages" / "contracts" / "jobs" / "radi144-api-job-record.schema.v1.json"
JOB_RECORD_INSTANCE = ROOT / "packages" / "contracts" / "jobs" / "radi144-api-job-record.v1.instance.json"
ROUTES = ROOT / "packages" / "contracts" / "routes" / "route-security-manifest.v1.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_WORKER_JOB_GATE_DECISION.md"
SERVICE = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "job_records.py"
ROUTE_FILE = ROOT / "apps" / "api" / "app" / "routes" / "radi144.py"
FORBIDDEN_RUNTIME_FILES = [
    ROOT / "apps" / "api" / "app" / "workers" / "radi144.py",
    ROOT / "apps" / "api" / "app" / "jobs" / "radi144.py",
]


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    schema = json.loads(JOB_RECORD_SCHEMA.read_text(encoding="utf-8"))
    instance = json.loads(JOB_RECORD_INSTANCE.read_text(encoding="utf-8"))
    routes = json.loads(ROUTES.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("api_job_records_enabled") is not True:
        fail("Radi144 API job records must be enabled")
    if runtime_scope.get("worker_jobs_enabled") is not False:
        fail("external worker_jobs_enabled must remain false")
    runtime_gate_opened = "radi144_worker_runtime_gate_decision" in project_text
    if runtime_scope.get("worker_runtime_enabled") is not runtime_gate_opened:
        fail("worker_runtime_enabled must match current worker runtime gate")
    if runtime_scope.get("engine_execution_enabled") is not False:
        fail("engine_execution_enabled must remain false")
    boundary = manifest.get("api_job_record_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/jobs/radi144-api-job-record.v1.instance.json":
        fail("Radi144 manifest must link API job record boundary")
    if boundary.get("schema_id") != instance.get("schema_id"):
        fail("Radi144 API job record boundary schema_id drift")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 API job record schema_id drift")
    if instance.get("api_job_records_enabled") is not True or instance.get("created_status") != "queued":
        fail("Radi144 API job record instance must create queued records")
    for flag in ["worker_runtime_enabled", "engine_execution_enabled", "result_writes_in_route_enabled", "projection_builder_in_create_route_enabled"]:
        if instance.get(flag) is not False:
            fail(f"Radi144 API job record must keep {flag} false")

    if "module_runs" not in set(Base.metadata.tables):
        fail("ModuleRun storage table must back API job records")
    if not SERVICE.is_file():
        fail("Radi144 job record service missing")
    service_text = SERVICE.read_text(encoding="utf-8")
    for token in ["Radi144JobRecordService", "create_or_get_job_record", "WorkflowStepRun", "status=\"queued\"", "await self.session.flush()"]:
        if token not in service_text:
            fail(f"Radi144 job record service missing token: {token}")
    for forbidden in ["commit()", "Radi144DomainService", "Radi144ResultWriter", "Radi144ProjectionBuilder"]:
        if forbidden in service_text:
            fail(f"Radi144 job record service must not execute/write/project: {forbidden}")

    runtime_route = next(
        (route for route in app.routes if isinstance(route, APIRoute) and route.path == "/engines/radi144/jobs" and "POST" in (route.methods or set())),
        None,
    )
    if runtime_route is None or runtime_route.name != "create_radi144_job_record":
        fail("Radi144 POST job route must create job records")
    route_text = ROUTE_FILE.read_text(encoding="utf-8")
    for token in ["Radi144JobRecordService", "create_or_get_job_record", "await session.commit()"]:
        if token not in route_text:
            fail(f"Radi144 job route missing token: {token}")
    for forbidden in ["Radi144DomainService", "Radi144ResultWriter"]:
        if forbidden in route_text:
            fail(f"Radi144 job route must not execute/write results: {forbidden}")

    route_manifest = next(route for route in routes.get("routes", []) if route.get("path") == "/engines/radi144/jobs")
    constraints = set(route_manifest.get("constraints", []))
    for required in ["tenant_context_required", "db_join_or_rls_required", "wrong_tenant_test_required", "job_record_write_enabled", "no_worker_runtime", "no_engine_execution", "no_runtime_result_writes"]:
        if required not in constraints:
            fail(f"Radi144 job route missing constraint: {required}")

    existing_runtime_files = [str(path.relative_to(ROOT)) for path in FORBIDDEN_RUNTIME_FILES if path.exists()]
    if existing_runtime_files:
        fail(f"Worker runtime files opened too early: {existing_runtime_files}")

    for token in ["radi144_worker_job_gate_decision", "status: api_job_records_enabled_without_worker_runtime", "radi144_worker_runtime_gate_decision"]:
        if token not in project_text:
            fail(f"Project anchor missing worker job token: {token}")
    for token in ["API job records", "no worker runtime", "engine execution remains blocked", "radi144_worker_runtime_gate_decision"]:
        if token not in decision_text:
            fail(f"Worker job doc missing token: {token}")

    print("[OK] Radi144 API job records are enabled through ModuleRun")
    print("[OK] Engine execution remains blocked")
    print("[OK] Job create route is tenant-scoped and does not write results")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
