"""Radi144 Result Persistence Gate Decision tests.

The original decision deferred storage until upstream engine job/API/projection
boundaries were decided. A later storage-only gate may supersede the no-table
condition while runtime writes remain blocked.
"""

import json
from pathlib import Path

from fastapi.routing import APIRoute

import app.models  # noqa: F401 - register SQLAlchemy metadata
from app.db.base import Base
from app.main import app

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
RESULT_SCHEMA = ROOT / "packages" / "contracts" / "results" / "radi144-result.schema.v1.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_RESULT_PERSISTENCE_GATE_DECISION.md"
MIGRATIONS = ROOT / "apps" / "api" / "alembic" / "versions"

CORE_STORAGE_TABLES = {"module_runs", "module_results", "module_provenances"}
DEFERRED_STORAGE_TABLES = {"module_inputs", "module_outputs"}


def test_persistence_decision_keeps_runtime_scope_closed() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    scope = manifest["runtime_scope"]

    assert scope["result_schema_enabled"] is True
    assert scope["result_persistence_enabled"] is False
    assert scope["client_projection_enabled"] is False
    assert scope["engine_api_enabled"] is False
    assert scope["engine_execution_enabled"] is False


def test_result_schema_has_persistence_prerequisite_metadata() -> None:
    schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))

    assert "retention" in schema["required"]
    assert "client_projection" in schema["required"]
    assert schema["properties"]["retention"]["properties"]["raw_debug_allowed"]["const"] is False
    assert schema["properties"]["client_projection"]["properties"]["status"]["enum"] == ["pending_projection_builder"]


def test_storage_decision_is_either_deferred_or_superseded_by_storage_gate() -> None:
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    storage_gate_opened = "radi144_result_persistence_storage_gate_decision" in project_text

    if storage_gate_opened:
        assert CORE_STORAGE_TABLES.issubset(set(Base.metadata.tables))
    else:
        assert not (CORE_STORAGE_TABLES & set(Base.metadata.tables))

    migration_text = "\n".join(path.read_text(encoding="utf-8") for path in MIGRATIONS.glob("*.py"))
    for table in DEFERRED_STORAGE_TABLES:
        assert table not in migration_text


def test_persistence_decision_does_not_open_routes() -> None:
    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    forbidden_fragments = {"/engines", "/engine", "/modules", "/results", "/radi144"}
    allowed_radi144_paths = {
        "/engines/radi144/jobs",
        "/engines/radi144/jobs/{job_id}",
        "/engines/radi144/jobs/{job_id}/result",
    }

    assert not [path for path in runtime_paths for fragment in forbidden_fragments if fragment in path and path not in allowed_radi144_paths]


def test_project_anchor_records_deferred_decision_and_next_gate() -> None:
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")

    assert "radi144_result_persistence_gate_decision:" in project_text
    assert "status: deferred_until_upstream_engine_gates" in project_text
    assert "radi144_engine_job_gate_decision" in project_text
    for blocker in ["result_persistence", "client_projection_builder", "engine_api", "worker_jobs", "engine_execution"]:
        assert f"- {blocker}" in project_text


def test_decision_doc_lists_required_upstream_gates() -> None:
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    for gate in [
        "radi144_result_schema_gate",
        "radi144_engine_job_gate",
        "radi144_engine_api_gate",
        "radi144_client_projection_gate",
    ]:
        assert gate in decision_text
