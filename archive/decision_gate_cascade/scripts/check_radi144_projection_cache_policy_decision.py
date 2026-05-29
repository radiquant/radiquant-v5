#!/usr/bin/env python3
"""Validate the Radi144 Projection Cache Policy Decision Gate."""

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
DECISION_SCHEMA = ROOT / "packages" / "contracts" / "projections" / "radi144-projection-cache-policy-decision.schema.v1.json"
DECISION_INSTANCE = ROOT / "packages" / "contracts" / "projections" / "radi144-projection-cache-policy-decision.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_PROJECTION_CACHE_POLICY_DECISION_GATE.md"
ENGINE_MODEL = ROOT / "apps" / "api" / "app" / "models" / "engine.py"
WORKER_RUNTIME = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "worker_runtime.py"
ROUTE_FILE = ROOT / "apps" / "api" / "app" / "routes" / "radi144.py"
MIGRATIONS = ROOT / "apps" / "api" / "alembic" / "versions"

FORBIDDEN_CACHE_TOKENS = {
    "ProjectionCache",
    "projection_cache_json",
    "projection_cache_key",
    "projection_cache_expires_at",
    "cached_projection",
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
    if runtime_scope.get("projection_cache_policy_recorded") is not True:
        fail("Radi144 projection cache policy decision must be recorded")
    if runtime_scope.get("api_projection_reads_enabled") is not True:
        fail("Radi144 API projection reads must remain enabled")
    for flag in ["projection_cache_enabled", "projection_cache_storage_enabled", "projection_cache_write_service_enabled", "materialized_projection_storage_enabled", "worker_projection_materialization_enabled"]:
        if runtime_scope.get(flag) is not False:
            fail(f"Radi144 runtime_scope {flag} must remain false")

    boundary = manifest.get("projection_cache_policy_decision_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/projections/radi144-projection-cache-policy-decision.v1.instance.json":
        fail("Radi144 manifest must link projection cache policy decision")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 projection cache policy schema_id drift")
    if boundary.get("schema_id") != instance.get("schema_id"):
        fail("Radi144 projection cache policy boundary schema_id drift")
    if instance.get("decision") != "record_no_cache_policy_until_storage_contract":
        fail("Radi144 projection cache policy must remain no-cache")
    if instance.get("cache_mode") != "no_cache_on_demand_projection_only":
        fail("Radi144 projection cache mode must remain on-demand only")
    if instance.get("required_future_gate") != "radi144_materialized_projection_storage_contract_gate_decision":
        fail("Radi144 projection cache policy must point to materialized storage contract future gate")
    for flag in ["projection_cache_enabled", "projection_cache_storage_enabled", "projection_cache_write_service_enabled"]:
        if instance.get(flag) is not False or boundary.get(flag) is not False:
            fail(f"Radi144 projection cache policy {flag} must remain false")
    required_triggers = set(instance.get("required_invalidation_triggers", []))
    for trigger in ["result_payload_rewritten", "retention_deleted", "consent_revoked", "role_policy_changed", "projection_builder_version_changed"]:
        if trigger not in required_triggers:
            fail(f"Radi144 projection cache policy missing invalidation trigger: {trigger}")

    tables = set(Base.metadata.tables)
    for forbidden_table in ["projection_cache", "projection_caches", "module_projection_cache"]:
        if forbidden_table in tables:
            fail(f"Projection cache table must remain absent: {forbidden_table}")

    model_text = ENGINE_MODEL.read_text(encoding="utf-8")
    worker_text = WORKER_RUNTIME.read_text(encoding="utf-8")
    route_text = ROUTE_FILE.read_text(encoding="utf-8")
    migration_text = "\n".join(path.read_text(encoding="utf-8") for path in MIGRATIONS.glob("*.py"))
    for token in FORBIDDEN_CACHE_TOKENS:
        if token in model_text or token in worker_text or token in route_text or token in migration_text:
            fail(f"Projection cache implementation token must remain absent: {token}")
    for required in ["Radi144ProjectionBuilder", "result_payload_json", "Radi144Result.model_validate"]:
        if required not in route_text:
            fail(f"API projection route must remain on-demand: {required}")

    for token in [
        "radi144_projection_cache_policy_gate_decision",
        "status: projection_cache_policy_recorded_cache_disabled",
        "radi144_materialized_projection_storage_contract_gate_decision",
    ]:
        if token not in project_text:
            fail(f"Project anchor missing projection cache policy token: {token}")
    for blocker in [
        "projection_cache_storage",
        "projection_cache_write_service",
        "materialized_projection_storage",
        "worker_projection_materialization",
        "raw_debug_projection_cache",
    ]:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["Cache storage remains disabled", "projection builder version changed", "radi144_materialized_projection_storage_contract_gate_decision"]:
        if token not in decision_text:
            fail(f"Projection cache policy doc missing token: {token}")

    print("[OK] Radi144 projection cache policy decision is recorded")
    print("[OK] Projection cache storage/write service remain blocked; API reads remain on-demand")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
