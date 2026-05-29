"""Radi144 Result Persistence Storage Gate tests.

The gate opens storage models/migrations only. Runtime writes, API routes,
projection builder, workers, and engine execution remain blocked.
"""

import json
from pathlib import Path

from fastapi.routing import APIRoute

import app.models  # noqa: F401 - register SQLAlchemy metadata
from app.db.base import Base
from app.main import app

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
STORAGE_SCHEMA = ROOT / "packages" / "contracts" / "storage" / "radi144-result-storage.schema.v1.json"
STORAGE_INSTANCE = ROOT / "packages" / "contracts" / "storage" / "radi144-result-storage.v1.instance.json"
RESULT_SCHEMA = ROOT / "packages" / "contracts" / "results" / "radi144-result.schema.v1.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_RESULT_PERSISTENCE_STORAGE_GATE.md"
MIGRATION = ROOT / "apps" / "api" / "alembic" / "versions" / "0007_engine_result_storage.py"

REQUIRED_TABLES = {"module_runs", "module_results", "module_provenances"}
FORBIDDEN_TABLES = {"module_inputs", "module_outputs", "engine_jobs"}
FORBIDDEN_COLUMNS = {"raw_debug", "debug_json", "internal_state", "client_vector", "raw_resonance_matrix", "normalized_matrix"}


def test_storage_gate_enables_storage_models_only() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    scope = manifest["runtime_scope"]

    assert scope["result_persistence_storage_enabled"] is True
    assert scope["result_persistence_enabled"] is False
    assert scope["engine_api_enabled"] is False
    assert scope["worker_jobs_enabled"] is False
    assert scope["engine_execution_enabled"] is False
    assert scope["client_projection_enabled"] is False


def test_storage_contract_and_instance_are_linked() -> None:
    schema = json.loads(STORAGE_SCHEMA.read_text(encoding="utf-8"))
    storage = json.loads(STORAGE_INSTANCE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert schema["properties"]["schema_id"]["const"] == storage["schema_id"]
    assert manifest["storage_boundary"]["instance_path"] == "packages/contracts/storage/radi144-result-storage.v1.instance.json"
    assert storage["status"] == "storage_model_initialized_runtime_writes_blocked"
    assert storage["storage_enabled"] is True
    assert storage["runtime_writes_enabled"] is False
    assert set(storage["tables"]) == REQUIRED_TABLES


def test_storage_tables_are_tenant_scoped_and_raw_debug_safe() -> None:
    tables = set(Base.metadata.tables)

    assert REQUIRED_TABLES.issubset(tables)
    assert not (FORBIDDEN_TABLES & tables)
    for table_name in REQUIRED_TABLES:
        table = Base.metadata.tables[table_name]
        assert "tenant_id" in table.columns
        assert not (FORBIDDEN_COLUMNS & set(table.columns))


def test_module_result_storage_has_retention_projection_and_provenance_links() -> None:
    module_runs = Base.metadata.tables["module_runs"]
    module_results = Base.metadata.tables["module_results"]
    module_provenances = Base.metadata.tables["module_provenances"]

    for column in ["tenant_id", "session_id", "workflow_run_id", "workflow_step_run_id", "module_id", "phase", "schema_id", "job_contract_schema_id"]:
        assert column in module_runs.columns
    for column in ["tenant_id", "module_run_id", "schema_id", "result_payload_json", "retention_json", "projection_status", "raw_debug_allowed", "client_projection_required"]:
        assert column in module_results.columns
    for column in ["tenant_id", "module_run_id", "algorithm_version", "manifest_version", "input_hash", "reference_matrix_version", "compute_backend", "duration_ms", "provenance_json"]:
        assert column in module_provenances.columns


def test_storage_migration_exists_without_runtime_tables() -> None:
    migration_text = MIGRATION.read_text(encoding="utf-8")

    for table_name in REQUIRED_TABLES:
        assert table_name in migration_text
    for table_name in FORBIDDEN_TABLES:
        assert table_name not in migration_text


def test_result_schema_keeps_retention_and_projection_placeholder() -> None:
    result_schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))

    assert "retention" in result_schema["required"]
    assert "client_projection" in result_schema["required"]
    assert result_schema["properties"]["client_projection"]["properties"]["status"]["enum"] == ["pending_projection_builder"]


def test_storage_gate_does_not_open_runtime_routes() -> None:
    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    forbidden_fragments = {"/engines", "/engine", "/modules", "/results", "/radi144", "/jobs"}
    allowed_radi144_paths = {
        "/engines/radi144/jobs",
        "/engines/radi144/jobs/{job_id}",
        "/engines/radi144/jobs/{job_id}/result",
    }

    assert not [path for path in runtime_paths for fragment in forbidden_fragments if fragment in path and path not in allowed_radi144_paths]


def test_project_anchor_and_doc_advance_to_api_runtime_route_decision() -> None:
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    assert "radi144_result_persistence_storage_gate_decision:" in project_text
    assert "status: storage_model_initialized_runtime_writes_blocked" in project_text
    assert "radi144_engine_api_runtime_route_gate_decision" in project_text
    for blocker in ["runtime_result_writes", "engine_api_runtime_routes", "client_projection_builder", "worker_jobs", "engine_execution"]:
        assert f"- {blocker}" in project_text
    for token in ["storage-only", "runtime writes remain blocked", "engine execution remains blocked"]:
        assert token in decision_text
