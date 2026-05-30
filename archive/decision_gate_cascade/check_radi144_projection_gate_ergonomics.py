#!/usr/bin/env python3
"""Validate Radi144 projection gate ergonomics anchors without opening runtime scope."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

import app.models  # noqa: F401,E402
from app.db.base import Base  # noqa: E402

PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
ERGONOMICS_DOC = ROOT / "docs" / "architecture" / "RADI144_PROJECTION_GATE_ERGONOMICS.md"
ENGINE_MODEL = ROOT / "apps" / "api" / "app" / "models" / "engine.py"
WORKER_RUNTIME = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "worker_runtime.py"
ROUTE_FILE = ROOT / "apps" / "api" / "app" / "routes" / "radi144.py"
MIGRATIONS = ROOT / "apps" / "api" / "alembic" / "versions"

FORBIDDEN_IMPLEMENTATION_TOKENS = {
    "class ModuleProjection",
    "__tablename__ = \"module_projections\"",
    "op.create_table(\"module_projections\"",
    "op.create_table('module_projections'",
    "ProjectionWriteService",
    "persist_projection",
}

REQUIRED_PROJECT_TOKENS = [
    "radi144_projection_gate_ergonomics:",
    "status: ergonomics_anchor_recorded",
    "scope: documentation_and_validation_only_no_runtime_change",
    "document: docs/architecture/RADI144_PROJECTION_GATE_ERGONOMICS.md",
    "validator: scripts/check_radi144_projection_gate_ergonomics.py",
    "tests: tests/test_radi144_projection_gate_ergonomics.py",

    "source_of_truth: module_results.result_payload_json",
    "projection_read_mode: on_demand_existing_api_projection_read_boundary",
    "safe_bundling: allowed_only_within_single_safety_boundary",
    "priority_order: accuracy_and_stability_before_speed",
    "completed_gate: radi144_materialized_projection_migration_file_repository_file_admission_gate_decision",
    "next_phase: radi144_materialized_projection_migration_file_repository_file_admission_implementation_gate_decision",
    "phase: radi144_materialized_projection_migration_file_repository_file_admission_implementation_gate_decision",
    "code_features_allowed: false",
]

REQUIRED_BLOCKERS = [
    "alembic_projection_migration",
    "module_projections_database_table",
    "materialized_projection_orm_model",
    "projection_write_service",
    "worker_projection_materialization",
    "projection_cache_storage",
    "raw_debug_internal_projection_storage",
    "new_projection_runtime_route",
    "gpu_cuda_execution",
    "api_triggered_execution",
    "external_queue_daemon_execution",
]

REQUIRED_CHECKLIST = [
    "contract_schema_exists_when_contract_bearing",
    "contract_instance_exists_when_contract_bearing",
    "radi144_manifest_links_contract_bearing_gate",
    "project_anchor_records_status_decision_doc_validator_tests_future_gate_invariants_blockers",
    "validator_fails_closed_on_forbidden_implementation_tokens",
    "test_runs_validator",
    "verify_bootstrap_includes_applicable_artifacts",
    "make_verify_green",
    "blocked_scopes_remain_blocked",
]

REQUIRED_DOC_TOKENS = [
    "ergonomics-only artifact",
    "Stable gate checklist",
    "Completed gate: `radi144_materialized_projection_migration_file_repository_file_admission_gate_decision`",
    "Next phase: `radi144_materialized_projection_migration_file_repository_file_admission_implementation_gate_decision`",
    "Source of truth: `module_results.result_payload_json`",
    "Safe future bundling policy",
    "Blocked scopes remain blocked",
]


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    doc_text = ERGONOMICS_DOC.read_text(encoding="utf-8")

    for token in REQUIRED_PROJECT_TOKENS:
        if token not in project_text:
            fail(f"Project ergonomics anchor missing token: {token}")
    for blocker in REQUIRED_BLOCKERS:
        if f"- {blocker}" not in project_text:
            fail(f"Project ergonomics anchor missing blocker: {blocker}")
    for item in REQUIRED_CHECKLIST:
        if f"- {item}" not in project_text:
            fail(f"Project ergonomics checklist missing item: {item}")
    for token in REQUIRED_DOC_TOKENS:
        if token not in doc_text:
            fail(f"Projection ergonomics doc missing token: {token}")

    if "module_projections" in set(Base.metadata.tables):
        fail("module_projections table must remain absent after ergonomics bundle")
    implementation_text = "\n".join([
        ENGINE_MODEL.read_text(encoding="utf-8"),
        WORKER_RUNTIME.read_text(encoding="utf-8"),
        ROUTE_FILE.read_text(encoding="utf-8"),
        "\n".join(path.read_text(encoding="utf-8") for path in MIGRATIONS.glob("*.py")),
    ])
    for token in FORBIDDEN_IMPLEMENTATION_TOKENS:
        if token in implementation_text:
            fail(f"Projection implementation must remain absent: {token}")

    print("[OK] Radi144 projection gate ergonomics anchor validates")
    print("[OK] Ergonomics bundle does not open migration, table, ORM, write service, worker materialization, or route")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
