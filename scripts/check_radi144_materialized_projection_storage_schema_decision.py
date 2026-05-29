#!/usr/bin/env python3
"""Validate the Radi144 Materialized Projection Storage Schema Decision Gate."""

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
DECISION_SCHEMA = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-storage-schema-decision.schema.v1.json"
DECISION_INSTANCE = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-storage-schema-decision.v1.instance.json"
STORAGE_SCHEMA = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-storage.schema.v1.json"
STORAGE_INSTANCE = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-storage.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_MATERIALIZED_PROJECTION_STORAGE_SCHEMA_DECISION_GATE.md"
ENGINE_MODEL = ROOT / "apps" / "api" / "app" / "models" / "engine.py"
WORKER_RUNTIME = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "worker_runtime.py"
ROUTE_FILE = ROOT / "apps" / "api" / "app" / "routes" / "radi144.py"
MIGRATIONS = ROOT / "apps" / "api" / "alembic" / "versions"

FORBIDDEN_IMPLEMENTATION_TOKENS = {
    "class ModuleProjection",
    "__tablename__ = \"module_projections\"",
    "op.create_table(\"module_projections\"",
    "ProjectionWriteService",
    "persist_projection",
}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    decision_schema = json.loads(DECISION_SCHEMA.read_text(encoding="utf-8"))
    decision = json.loads(DECISION_INSTANCE.read_text(encoding="utf-8"))
    storage_schema = json.loads(STORAGE_SCHEMA.read_text(encoding="utf-8"))
    storage_instance = json.loads(STORAGE_INSTANCE.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("materialized_projection_storage_schema_recorded") is not True:
        fail("Radi144 materialized projection storage schema must be recorded")
    for flag in ["storage_implementation_enabled", "projection_storage_tables_enabled", "projection_write_service_enabled", "worker_projection_materialization_enabled"]:
        if runtime_scope.get(flag) is not False:
            fail(f"Radi144 runtime_scope {flag} must remain false")

    boundary = manifest.get("materialized_projection_storage_schema_decision_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/projections/radi144-materialized-projection-storage-schema-decision.v1.instance.json":
        fail("Radi144 manifest must link materialized projection storage schema decision")
    if decision_schema.get("properties", {}).get("schema_id", {}).get("const") != decision.get("schema_id"):
        fail("Radi144 materialized projection storage schema decision schema_id drift")
    if boundary.get("schema_id") != decision.get("schema_id"):
        fail("Radi144 materialized projection storage schema decision boundary schema_id drift")
    if decision.get("decision") != "record_storage_schema_without_implementation":
        fail("Radi144 storage schema decision must not enable implementation")
    if decision.get("required_future_gate") != "radi144_materialized_projection_storage_migration_gate_decision":
        fail("Radi144 storage schema decision must point to migration future gate")
    for flag in ["storage_implementation_enabled", "projection_storage_tables_enabled", "projection_write_service_enabled", "worker_projection_materialization_enabled"]:
        if decision.get(flag) is not False or boundary.get(flag) is not False:
            fail(f"Radi144 storage schema decision {flag} must remain false")

    if storage_schema.get("properties", {}).get("schema_id", {}).get("const") != storage_instance.get("schema_id"):
        fail("Radi144 materialized projection storage schema_id drift")
    required = set(storage_schema.get("required", []))
    for field in ["tenant_id", "module_run_id", "module_result_id", "role", "projection_schema_id", "projection_builder_version", "source_result_hash", "retention", "projection_payload", "invalidated_at"]:
        if field not in required:
            fail(f"Radi144 materialized projection storage schema missing field: {field}")
    if storage_schema.get("properties", {}).get("projection_payload", {}).get("properties", {}).get("raw_debug_excluded", {}).get("const") is not True:
        fail("Radi144 materialized projection storage schema must require raw_debug_excluded")
    if storage_schema.get("properties", {}).get("retention", {}).get("properties", {}).get("raw_debug_allowed", {}).get("const") is not False:
        fail("Radi144 materialized projection storage schema must forbid raw debug retention")
    for flag in ["storage_implementation_enabled", "projection_write_service_enabled", "worker_projection_materialization_enabled"]:
        if storage_instance.get(flag) is not False:
            fail(f"Radi144 materialized projection storage instance {flag} must remain false")
    if storage_instance.get("projection_payload", {}).get("raw_debug_excluded") is not True:
        fail("Radi144 materialized projection storage instance must exclude raw debug")

    if "module_projections" in set(Base.metadata.tables):
        fail("module_projections table must remain absent in schema-only gate")
    implementation_text = "\n".join([
        ENGINE_MODEL.read_text(encoding="utf-8"),
        WORKER_RUNTIME.read_text(encoding="utf-8"),
        ROUTE_FILE.read_text(encoding="utf-8"),
        "\n".join(path.read_text(encoding="utf-8") for path in MIGRATIONS.glob("*.py")),
    ])
    for token in FORBIDDEN_IMPLEMENTATION_TOKENS:
        if token in implementation_text:
            fail(f"Projection storage implementation must remain absent: {token}")

    for token in [
        "radi144_materialized_projection_storage_schema_gate_decision",
        "status: storage_schema_recorded_implementation_disabled",
        "radi144_materialized_projection_storage_migration_gate_decision",
    ]:
        if token not in project_text:
            fail(f"Project anchor missing storage schema token: {token}")
    for blocker in ["materialized_projection_storage_table", "projection_storage_migration", "projection_write_service", "worker_projection_materialization", "raw_debug_projection_storage"]:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["No ORM model", "raw_debug_excluded: true", "radi144_materialized_projection_storage_migration_gate_decision"]:
        if token not in decision_text:
            fail(f"Storage schema doc missing token: {token}")

    print("[OK] Radi144 materialized projection storage schema is recorded")
    print("[OK] Schema-only gate did not open ORM models, migrations, write services, workers, or routes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
