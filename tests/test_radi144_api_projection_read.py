"""Radi144 API Projection Read Gate tests."""

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db_session, make_async_engine
from app.main import create_app
from app.models.client import ClientProfile
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus
from app.models.session import ClientSession, SessionGoal, SessionStatus
from app.models.workflow import WorkflowRun, WorkflowRunStatus, WorkflowStepRun, WorkflowStepRunStatus
from app.schemas.radi144_result import (
    Radi144ClientProjectionPlaceholder,
    Radi144Confidence,
    Radi144Provenance,
    Radi144Result,
    Radi144Retention,
    Radi144SynergySeed,
)
from app.security.passwords import hash_password
from app.services.auth import AuthService, get_auth_service
from app.services.radi144 import Radi144ResultWriter
from app.services.radi144.projection_write_service import ProjectionWriteService


@pytest_asyncio.fixture
async def projection_app() -> AsyncIterator[tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService]]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    settings = Settings(DATABASE_URL="sqlite+aiosqlite:///:memory:", SECRET_KEY=SecretStr("projection-read-secret-minimum-32-characters"), ACCESS_TOKEN_TTL_MINUTES=5)
    auth_service = AuthService(settings=settings)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    app = create_app()

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    try:
        yield app, factory, auth_service
    finally:
        await engine.dispose()


def _headers(auth_service: AuthService, tenant: Tenant, user: User) -> dict[str, str]:
    token = auth_service.issue_access_token(user_id=user.id, tenant_id=tenant.id, role=RoleName.THERAPIST)
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant.id)}


async def _seed_result(factory: async_sessionmaker[AsyncSession]) -> tuple[Tenant, User, Radi144Result]:
    async with factory() as session:
        tenant = Tenant(slug="tenant-a", name="Tenant A", status=TenantStatus.ACTIVE)
        role = Role(name=RoleName.THERAPIST, description="Therapist")
        session.add_all([tenant, role])
        await session.flush()
        user = User(tenant_id=tenant.id, role_id=role.id, email="a@example.com", display_name="Therapist", password_hash=hash_password("safe-password-123", iterations=1), status=UserStatus.ACTIVE, is_mfa_enabled=False)
        session.add(user)
        await session.flush()
        client = ClientProfile(tenant_id=tenant.id, display_name="Client A", created_by_user_id=user.id, updated_by_user_id=user.id)
        session.add(client)
        await session.flush()
        goal = SessionGoal(tenant_id=tenant.id, client_id=client.id, title="Wellbeing focus", description="", created_by_user_id=user.id)
        session.add(goal)
        await session.flush()
        client_session = ClientSession(tenant_id=tenant.id, client_id=client.id, goal_id=goal.id, status=SessionStatus.ACTIVE, created_by_user_id=user.id, updated_by_user_id=user.id)
        session.add(client_session)
        await session.flush()
        workflow_run = WorkflowRun(tenant_id=tenant.id, session_id=client_session.id, workflow_id="W-A", workflow_slug="quick-diagnosis", status=WorkflowRunStatus.PLANNED, created_by_user_id=user.id, updated_by_user_id=user.id)
        session.add(workflow_run)
        await session.flush()
        step = WorkflowStepRun(tenant_id=tenant.id, workflow_run_id=workflow_run.id, step_index=0, module_id="radi144", phase="diagnose", status=WorkflowStepRunStatus.PLANNED)
        session.add(step)
        await session.flush()
        result = Radi144Result(
            module_run_id=uuid4(),
            tenant_id=tenant.id,
            client_id=client.id,
            session_id=client_session.id,
            workflow_run_id=workflow_run.id,
            algorithm_version="radi144-domain-v1",
            manifest_version="1.0.0",
            compute_backend="simulation_disabled_until_engine_gate",
            coherence_scores={f"label_{index}": 0.1 for index in range(12)},
            biofield_map={f"label_{index}": 0.1 for index in range(12)},
            confidence=Radi144Confidence(score=0.72, data_quality=0.6, stability=0.7),
            synergy_seed=Radi144SynergySeed(top_labels=["label_0", "label_1", "label_2"], confidence_score=0.72, seed_checksum="1234567890abcdef"),
            provenance=Radi144Provenance(algorithm_version="radi144-domain-v1", manifest_version="1.0.0", input_hash="1234567890abcdef", reference_matrix_version="radi144-reference-v1", compute_backend="simulation_disabled_until_engine_gate", duration_ms=0),
            retention=Radi144Retention(),
            client_projection=Radi144ClientProjectionPlaceholder(summary_label="Projection pending", quality_label="wellbeing quality pending"),
        )
        await Radi144ResultWriter(session).persist_result(result=result, workflow_step_run_id=step.id)
        await ProjectionWriteService(session).persist_projection(module_run_id=result.module_run_id, tenant_id=result.tenant_id)
        await session.commit()
        return tenant, user, result


@pytest.mark.asyncio
async def test_result_endpoint_returns_client_projection(projection_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService]) -> None:
    app, factory, auth_service = projection_app
    tenant, user, result = await _seed_result(factory)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/engines/radi144/jobs/{result.module_run_id}/result?role=client", headers=_headers(auth_service, tenant, user))

    assert response.status_code == 200
    body = response.json()
    assert body["projection"] == "calm_summary"
    assert body["raw_debug_excluded"] is True
    for forbidden in ["raw_debug", "debug_json", "internal_state", "client_vector", "raw_resonance_matrix", "normalized_matrix"]:
        assert forbidden not in body


@pytest.mark.asyncio
async def test_result_endpoint_returns_therapist_projection(projection_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService]) -> None:
    app, factory, auth_service = projection_app
    tenant, user, result = await _seed_result(factory)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/engines/radi144/jobs/{result.module_run_id}/result?role=therapist", headers=_headers(auth_service, tenant, user))

    assert response.status_code == 200
    body = response.json()
    assert body["projection"] == "professional_detail"
    assert body["retention"]["raw_debug_allowed"] is False
    assert "raw_resonance_matrix" not in str(body)


@pytest.mark.asyncio
async def test_result_endpoint_is_tenant_scoped(projection_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService]) -> None:
    app, factory, auth_service = projection_app
    tenant, user, result = await _seed_result(factory)
    other_tenant = Tenant(id=uuid4(), slug="tenant-b", name="Tenant B", status=TenantStatus.ACTIVE)
    other_user = User(id=uuid4(), tenant_id=other_tenant.id, role_id=user.role_id, email="b@example.com", display_name="Other", password_hash="unused", status=UserStatus.ACTIVE, is_mfa_enabled=False)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/engines/radi144/jobs/{result.module_run_id}/result", headers=_headers(auth_service, other_tenant, other_user))

    assert response.status_code == 404
