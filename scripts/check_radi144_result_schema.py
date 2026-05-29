#!/usr/bin/env python3
"""Validate the Radi144 Result Schema Gate without persistence or API routes."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import uuid4

from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.main import app  # noqa: E402
from app.schemas.radi144_result import (  # noqa: E402
    Radi144ClientProjectionPlaceholder,
    Radi144Confidence,
    Radi144Provenance,
    Radi144Result,
    Radi144Retention,
    Radi144SynergySeed,
)

MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
RESULT_SCHEMA = ROOT / "packages" / "contracts" / "results" / "radi144-result.schema.v1.json"
ALLOWED_RADI144_RUNTIME_PATHS = {
    "/engines/radi144/jobs",
    "/engines/radi144/jobs/{job_id}",
    "/engines/radi144/jobs/{job_id}/result",
}
FORBIDDEN_PATH_FRAGMENTS = {"/engines", "/engine", "/modules", "/results", "/radi144"}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("result_schema_enabled") is not True:
        fail("Radi144 result schema flag must be enabled")
    for blocked_flag in ["result_persistence_enabled", "client_projection_enabled", "engine_api_enabled", "engine_execution_enabled"]:
        if runtime_scope.get(blocked_flag) is not False:
            fail(f"{blocked_flag} must remain false")

    result_contract = manifest.get("result_contract", {})
    if result_contract.get("schema_path") != "packages/contracts/results/radi144-result.schema.v1.json":
        fail("Radi144 manifest must point to committed result schema")
    if result_contract.get("raw_debug_allowed") is not False or result_contract.get("client_projection_required") is not True:
        fail("Radi144 result privacy flags are incomplete")

    for field in result_contract.get("required_fields", []):
        if field not in schema.get("required", []):
            fail(f"Manifest required field missing in result schema: {field}")
    for field in ["retention", "client_projection", "provenance"]:
        if field not in schema.get("required", []):
            fail(f"Radi144 result schema must require {field}")

    sample = Radi144Result(
        module_run_id=uuid4(),
        tenant_id=uuid4(),
        client_id=uuid4(),
        session_id=uuid4(),
        workflow_run_id=uuid4(),
        algorithm_version="radi144-domain-v1",
        manifest_version=manifest["version"],
        compute_backend="simulation_disabled_until_engine_gate",
        coherence_scores={f"label_{index}": 0.1 for index in range(12)},
        biofield_map={f"label_{index}": 0.1 for index in range(12)},
        confidence=Radi144Confidence(score=0.5, data_quality=0.5, stability=0.5),
        synergy_seed=Radi144SynergySeed(
            top_labels=["label_0", "label_1", "label_2"],
            confidence_score=0.5,
            seed_checksum="1234567890abcdef",
        ),
        provenance=Radi144Provenance(
            algorithm_version="radi144-domain-v1",
            manifest_version=manifest["version"],
            input_hash="1234567890abcdef",
            reference_matrix_version="radi144-reference-v1",
            compute_backend="simulation_disabled_until_engine_gate",
            duration_ms=0,
        ),
        retention=Radi144Retention(),
        client_projection=Radi144ClientProjectionPlaceholder(
            summary_label="Projection builder pending",
            quality_label="wellbeing quality pending",
        ),
    )
    payload = sample.model_dump(mode="json")
    if "raw_debug" in payload:
        fail("Radi144 result payload must not expose top-level raw_debug data")
    forbidden_payload_text = json.dumps(payload)
    for forbidden in ["debug_json", "internal_state", "password", "access_token"]:
        if forbidden in forbidden_payload_text:
            fail(f"Radi144 result payload contains forbidden label: {forbidden}")

    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    allowed_paths = ALLOWED_RADI144_RUNTIME_PATHS if runtime_scope.get("engine_api_runtime_routes_enabled") is True else set()
    forbidden_paths = sorted(path for path in runtime_paths for fragment in FORBIDDEN_PATH_FRAGMENTS if fragment in path and path not in allowed_paths)
    if forbidden_paths:
        fail(f"Radi144 result/API routes must remain blocked: {forbidden_paths}")

    print("[OK] Radi144 result schema requires manifest fields, provenance, retention, and projection placeholder")
    print("[OK] Radi144 result DTO validates sample payload without raw/debug/internal labels")
    print("[OK] Radi144 result persistence, projection builder, API, and execution remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
