"""Radi144 Domain Service Gate tests.

The domain service is pure and side-effect free. It is not exposed through API
routes, workers, persistence, or engine execution in this gate.
"""

import pytest
from fastapi.routing import APIRoute

from app.main import app
from app.services.radi144 import Radi144DomainService, Radi144InputContext, Radi144ReferenceVector
from app.services.radi144.domain import MATRIX_SIZE, VECTOR_DIMENSIONS, Radi144DomainError


def _context() -> Radi144InputContext:
    return Radi144InputContext(
        tenant_id="tenant-a",
        client_id="client-a",
        session_id="session-a",
        goal_title="Ruhige Fokussierung",
        goal_description="Sanfter Start in eine Wellbeing-orientierte Sitzung.",
        client_display_name="Klient A",
    )


def test_radi144_domain_service_builds_deterministic_plan() -> None:
    service = Radi144DomainService()

    first = service.build_plan(_context())
    second = service.build_plan(_context())

    assert first == second
    assert len(first.client_vector) == VECTOR_DIMENSIONS
    assert len(first.reference_vectors) == MATRIX_SIZE
    assert len(first.normalized_matrix) == MATRIX_SIZE
    assert all(len(row) == MATRIX_SIZE for row in first.normalized_matrix)
    assert first.synergy_seed["source_module"] == "radi144"
    assert first.synergy_seed["matrix_shape"] == [12, 12]
    assert first.confidence["language_scope"] == "wellbeing_only"


def test_radi144_matrix_is_symmetric_clamped_and_has_unit_diagonal() -> None:
    plan = Radi144DomainService().build_plan(_context())

    for row_index, row in enumerate(plan.normalized_matrix):
        for column_index, value in enumerate(row):
            assert -1.0 <= value <= 1.0
            if row_index == column_index:
                assert value == 1.0
            else:
                assert value == plan.normalized_matrix[column_index][row_index]


def test_radi144_outputs_projection_safe_scores_without_raw_debug() -> None:
    plan = Radi144DomainService().build_plan(_context())

    assert set(plan.coherence_scores) == set(plan.biofield_map)
    assert len(plan.biofield_map) == MATRIX_SIZE
    assert "raw_debug" not in plan.synergy_seed
    assert "internal_state" not in plan.synergy_seed
    top_labels = plan.synergy_seed["top_labels"]
    assert isinstance(top_labels, list)
    assert len(top_labels) == 3


def test_radi144_domain_service_rejects_missing_analysis_consent() -> None:
    service = Radi144DomainService()
    context = Radi144InputContext(
        tenant_id="tenant-a",
        client_id="client-a",
        session_id="session-a",
        goal_title="Ruhige Fokussierung",
        consent_purpose="harmonization",
    )

    with pytest.raises(Radi144DomainError, match="analysis consent"):
        service.build_plan(context)


def test_radi144_domain_service_rejects_invalid_reference_catalog() -> None:
    service = Radi144DomainService()
    bad_references = (
        Radi144ReferenceVector(id="duplicate", label="one", values=tuple([1.0] * VECTOR_DIMENSIONS)),
        Radi144ReferenceVector(id="duplicate", label="two", values=tuple([1.0] * VECTOR_DIMENSIONS)),
    )

    with pytest.raises(Radi144DomainError, match="exactly 12"):
        service.build_plan(_context(), reference_vectors=bad_references)


def test_radi144_domain_service_does_not_open_engine_routes() -> None:
    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    forbidden_fragments = {"/engines", "/engine", "/modules", "/results", "/radi144"}
    allowed_radi144_paths = {
        "/engines/radi144/jobs",
        "/engines/radi144/jobs/{job_id}",
        "/engines/radi144/jobs/{job_id}/result",
    }

    assert not [path for path in runtime_paths for fragment in forbidden_fragments if fragment in path and path not in allowed_radi144_paths]
