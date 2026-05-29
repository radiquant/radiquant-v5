#!/usr/bin/env python3
"""Validate the Radi144 Materialized Projection Storage Decision Gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

import app.models  # noqa: F401,E402 - register ORM metadata
from app.db.base import Base  # noqa: E402

MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
DECISION_SCHEMA = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-storage-decision.schema.v1.json"
DECISION_INSTANCE = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-storage-decision.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_MATERIALIZED_PROJECTION_STORAGE_DECISION_GATE.md"
ENGINE_MODEL = ROOT / "apps" / "api" / "app" / "models" / "engine.py"
WORKER_RUNTIME = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "worker_runtime.py"
ROUTE_FILE = ROOT / "apps" / "api" / "app" / "routes" / "radi144.py"
MIGRATIONS = ROOT / "apps" / "api" / "alembic" / "versions"

FORBIDDEN_STORAGE_TOKENS = {
    "module_projections",
    "ModuleProjection",
    "projection_payload_json",
    "projection_cache",
    "materialized_projection",
}
FORBIDDEN_WORKER_TOKENS = {
    "Radi144ProjectionBuilder",
    "build_projection(",
    "projection_payload",
    "ModuleProjection",
    "projection_cache",
}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    schema = json.loads(DECISION_SCHEMA.read_text(encoding="utf-8"))
    instance = json.loads(DECISION_INSTANCE.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("materialized_projection_storage_decision_recorded") is not True:
        fail("Radi144 materialized projection storage decision must be recorded")
    if runtime_scope.get("api_projection_reads_enabled") is not True:
        fail("Radi144 API projection reads must remain enabled")
    for flag in [
        "materialized_projection_storage_enabled",
        "projection_storage_tables_enabled",
        "projection_write_service_enabled",
        "worker_projection_materialization_enabled",
    ]:
        if runtime_scope.get(flag) is not False:
            fail(f"Radi144 runtime_scope {flag} must remain false")

    boundary = manifest.get("materialized_projection_storage_decision_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/projections/radi144-materialized-projection-storage-decision.v1.instance.json":
        fail("Radi144 manifest must link materialized projection storage decision")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 materialized projection storage schema_id drift")
    if boundary.get("schema_id") != instance.get("schema_id"):
        fail("Radi144 materialized projection storage boundary schema_id drift")
    if instance.get("decision") != "defer_materialized_projection_storage_until_cache_policy_gate":
        fail("Radi144 materialized projection storage must be deferred")
    if instance.get("source_of_truth") != "module_results.result_payload_json":
        fail("Radi144 projection source of truth must remain stored result payload")
    if instance.get("required_future_gate") != "radi144_projection_cache_policy_gate_decision":
        fail("Radi144 materialized projection storage must point to cache policy future gate")
    for flag in [
        "materialized_projection_storage_enabled",
        "projection_storage_tables_enabled",
        "projection_write_service_enabled",
        "worker_projection_materialization_enabled",
    ]:
        if instance.get(flag) is not False or boundary.get(flag) is not False:
            fail(f"Radi144 materialized projection storage {flag} must remain false")

    tables = set(Base.metadata.tables)
    for forbidden_table in ["module_projections", "projection_cache", "projection_payloads"]:
        if forbidden_table in tables:
            fail(f"Materialized projection table must remain absent: {forbidden_table}")

    model_text = ENGINE_MODEL.read_text(encoding="utf-8")
    worker_text = WORKER_RUNTIME.read_text(encoding="utf-8")
    route_text = ROUTE_FILE.read_text(encoding="utf-8")
    migration_text = "\n".join(path.read_text(encoding="utf-8") for path in MIGRATIONS.glob("*.py"))
    for token in FORBIDDEN_STORAGE_TOKENS:
        if token in model_text or token in migration_text:
            fail(f"Projection storage token must remain absent from models/migrations: {token}")
    for token in FORBIDDEN_WORKER_TOKENS:
        if token in worker_text:
            fail(f"Worker must not write/materialize projections: {token}")
    for required in ["Radi144ProjectionBuilder", "result_payload_json", "Radi144Result.model_validate"]:
        if required not in route_text:
            fail(f"API projection route must remain on-demand: {required}")
    for forbidden in ["ModuleProjection", "projection_payload_json", "projection_cache"]:
        if forbidden in route_text:
            fail(f"API projection route must not read materialized projection storage: {forbidden}")

    for token in [
        "radi144_materialized_projection_storage_gate_decision",
        "status: materialized_projection_storage_deferred_on_demand_projection_only",
        "radi144_projection_cache_policy_gate_decision",
    ]:
        if token not in project_text:
            fail(f"Project anchor missing materialized projection storage token: {token}")
    for blocker in [
        "materialized_projection_storage",
        "projection_storage_tables",
        "projection_write_service",
        "worker_projection_materialization",
        "raw_debug_projection_storage",
    ]:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["conservative no-go", "No materialized projection table", "radi144_projection_cache_policy_gate_decision"]:
        if token not in decision_text:
            fail(f"Materialized projection storage doc missing token: {token}")

    print("[OK] Radi144 materialized projection storage decision is recorded conservatively")
    print("[OK] Projection storage tables/write services remain blocked; API reads remain on-demand")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
