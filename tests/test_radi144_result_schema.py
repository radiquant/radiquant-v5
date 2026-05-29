"""Radi144 Result Schema Gate tests.

This gate defines the result DTO/JSON schema only. It does not persist results,
open engine API routes, or build client projections.
"""

import json
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.routing import APIRoute
from pydantic import ValidationError

from app.main import app
from app.schemas.radi144_result import (
    Radi144ClientProjectionPlaceholder,
    Radi144Confidence,
    Radi144Provenance,
    Radi144Result,
    Radi144Retention,
    Radi144SynergySeed,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
RESULT_SCHEMA = ROOT / "packages" / "contracts" / "results" / "radi144-result.schema.v1.json"


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _sample_result() -> Radi144Result:
    manifest = _manifest()
    return Radi144Result(
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
        confidence=Radi144Confidence(score=0.5, data_quality=0.6, stability=0.7),
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


def test_radi144_result_schema_is_linked_from_manifest() -> None:
    manifest = _manifest()
    schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))

    assert manifest["runtime_scope"]["result_schema_enabled"] is True
    assert manifest["runtime_scope"]["result_persistence_enabled"] is False
    assert manifest["result_contract"]["schema_path"] == "packages/contracts/results/radi144-result.schema.v1.json"
    assert manifest["result_contract"]["schema_id"] == schema["properties"]["schema_id"]["const"]
    assert set(manifest["result_contract"]["required_fields"]).issubset(set(schema["required"]))


def test_radi144_result_dto_accepts_contract_sample() -> None:
    result = _sample_result()

    assert result.schema_id == "radi144_result_v1"
    assert result.module_id == "radi144"
    assert result.matrix_shape == (12, 12)
    assert result.retention.raw_debug_allowed is False
    assert result.retention.client_projection_required is True
    assert result.client_projection.status == "pending_projection_builder"


def test_radi144_result_dto_forbids_extra_raw_debug_fields() -> None:
    payload = _sample_result().model_dump(mode="json")
    payload["raw_debug"] = {"blocked": True}

    with pytest.raises(ValidationError):
        Radi144Result.model_validate(payload)


def test_radi144_result_dto_requires_projection_placeholder() -> None:
    payload = _sample_result().model_dump(mode="json")
    payload.pop("client_projection")

    with pytest.raises(ValidationError):
        Radi144Result.model_validate(payload)


def test_radi144_result_payload_contains_no_forbidden_labels() -> None:
    payload_text = json.dumps(_sample_result().model_dump(mode="json"))

    assert "raw_debug" not in _sample_result().model_dump(mode="json")
    for forbidden in ["debug_json", "internal_state", "password", "access_token"]:
        assert forbidden not in payload_text


def test_radi144_result_schema_does_not_open_result_or_engine_routes() -> None:
    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    forbidden_fragments = {"/engines", "/engine", "/modules", "/results", "/radi144"}
    allowed_radi144_paths = {
        "/engines/radi144/jobs",
        "/engines/radi144/jobs/{job_id}",
        "/engines/radi144/jobs/{job_id}/result",
    }

    assert not [path for path in runtime_paths for fragment in forbidden_fragments if fragment in path and path not in allowed_radi144_paths]
