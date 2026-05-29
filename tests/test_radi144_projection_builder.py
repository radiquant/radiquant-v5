"""Radi144 Projection Builder Gate tests."""

import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.schemas.radi144_result import (
    Radi144ClientProjectionPlaceholder,
    Radi144Confidence,
    Radi144Provenance,
    Radi144Result,
    Radi144Retention,
    Radi144SynergySeed,
)
from app.services.radi144.projection_builder import Radi144ProjectionBuilder, Radi144ProjectionError

ROOT = Path(__file__).resolve().parents[1]
BUILDER_INSTANCE = ROOT / "packages" / "contracts" / "projections" / "radi144-projection-builder.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"


def _result() -> Radi144Result:
    return Radi144Result(
        module_run_id=uuid4(),
        tenant_id=uuid4(),
        client_id=uuid4(),
        session_id=uuid4(),
        workflow_run_id=uuid4(),
        algorithm_version="radi144-domain-v1",
        manifest_version="1.0.0",
        compute_backend="simulation_disabled_until_engine_gate",
        coherence_scores={f"label_{index}": 0.1 for index in range(12)},
        biofield_map={f"label_{index}": 0.1 for index in range(12)},
        confidence=Radi144Confidence(score=0.72, data_quality=0.6, stability=0.7),
        synergy_seed=Radi144SynergySeed(top_labels=["label_0", "label_1", "label_2"], confidence_score=0.72, seed_checksum="1234567890abcdef"),
        provenance=Radi144Provenance(
            algorithm_version="radi144-domain-v1",
            manifest_version="1.0.0",
            input_hash="1234567890abcdef",
            reference_matrix_version="radi144-reference-v1",
            compute_backend="simulation_disabled_until_engine_gate",
            duration_ms=0,
        ),
        retention=Radi144Retention(),
        client_projection=Radi144ClientProjectionPlaceholder(summary_label="Projection pending", quality_label="wellbeing quality pending"),
    )


def test_projection_builder_creates_calm_client_summary_without_raw_debug() -> None:
    projection = Radi144ProjectionBuilder().build_client_projection(_result())
    payload = projection.model_dump(mode="json")

    assert projection.role == "client"
    assert projection.projection == "calm_summary"
    assert projection.confidence_band == "steady"
    assert projection.raw_debug_excluded is True
    assert len(projection.wellbeing_focus_labels) == 3
    for forbidden in ["raw_debug", "debug_json", "internal_state", "client_vector", "raw_resonance_matrix", "normalized_matrix"]:
        assert forbidden not in payload


def test_projection_builder_creates_therapist_detail_without_raw_matrices() -> None:
    projection = Radi144ProjectionBuilder().build_therapist_projection(_result())
    payload_text = str(projection.model_dump(mode="json"))

    assert projection.role == "therapist"
    assert projection.projection == "professional_detail"
    assert projection.confidence["language_scope"] == "wellbeing_only"
    assert projection.retention["raw_debug_allowed"] is False
    for forbidden in ["raw_debug':", "debug_json", "internal_state", "client_vector", "raw_resonance_matrix", "normalized_matrix"]:
        assert forbidden not in payload_text


def test_projection_builder_rejects_forbidden_payload_keys() -> None:
    result = _result().model_copy(update={"biofield_map": {**_result().biofield_map, "raw_debug": 0.1}})

    with pytest.raises(Radi144ProjectionError) as exc_info:
        Radi144ProjectionBuilder().build_client_projection(result)

    assert exc_info.value.reason == "forbidden_projection_key:raw_debug"


def test_projection_builder_contract_matches_projection_read_gate() -> None:
    builder = json.loads(BUILDER_INSTANCE.read_text(encoding="utf-8"))
    read_gate_opened = "radi144_api_projection_read_gate_decision" in PROJECT_ANCHOR.read_text(encoding="utf-8")

    assert builder["api_projection_reads_enabled"] is read_gate_opened
    assert builder["worker_jobs_enabled"] is False
    assert builder["engine_execution_enabled"] is False
