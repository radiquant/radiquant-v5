"""RadiMorphic API route tests."""

import sys
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

import app.models  # noqa: F401, E402
import app.models.radimorphic  # noqa: F401, E402
from app.core.config import Settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db_session, make_async_engine  # noqa: E402
from app.models.client import ClientProfile  # noqa: E402
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus  # noqa: E402
from app.models.session import ClientSession, SessionGoal, SessionStatus  # noqa: E402
from app.models.workflow import (  # noqa: E402
    WorkflowRun,
    WorkflowRunStatus,
    WorkflowStepRun,
    WorkflowStepRunStatus,
)
from app.routes.radimorphic import router as radimorphic_router  # noqa: E402
from app.services.auth import AuthService, get_auth_service  # noqa: E402
from app.services.radimorphic.engine import RadiMorphicEngine  # noqa: E402
from app.services.radimorphic.worker_runtime import (  # noqa: E402
    RadiMorphicWorkerRuntimeService,
)


@pytest_asyncio.fixture
async def radimorphic_api() -> AsyncIterator[
    tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService]
]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    auth_service = AuthService(
        settings=Settings(
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
            SECRET_KEY=SecretStr("radimorphic-api-secret-minimum-32-characters"),
            ACCESS_TOKEN_TTL_MINUTES=5,
        )
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    app = FastAPI()

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.include_router(radimorphic_router)

    try:
        yield app, factory, auth_service
    finally:
        await engine.dispose()


async def _seed_context(
    factory: async_sessionmaker[AsyncSession],
    *,
    slug: str,
) -> tuple[UUID, UUID, UUID, UUID, UUID]:
    async with factory() as session:
        tenant = Tenant(slug=slug, name=slug.title(), status=TenantStatus.ACTIVE)
        role = await session.scalar(select(Role).where(Role.name == RoleName.THERAPIST))
        if role is None:
            role = Role(name=RoleName.THERAPIST, description="Therapist")
            session.add(role)
        session.add(tenant)
        await session.flush()
        user = User(
            tenant_id=tenant.id,
            role_id=role.id,
            email=f"{slug}@example.com",
            display_name="Therapist",
            password_hash="not-used",
            status=UserStatus.ACTIVE,
            is_mfa_enabled=False,
        )
        session.add(user)
        await session.flush()
        client = ClientProfile(
            tenant_id=tenant.id,
            display_name=f"Client {slug}",
            created_by_user_id=user.id,
            updated_by_user_id=user.id,
        )
        session.add(client)
        await session.flush()
        goal = SessionGoal(
            tenant_id=tenant.id,
            client_id=client.id,
            title="Wellbeing focus",
            description="Centered session",
            created_by_user_id=user.id,
        )
        session.add(goal)
        await session.flush()
        client_session = ClientSession(
            tenant_id=tenant.id,
            client_id=client.id,
            goal_id=goal.id,
            status=SessionStatus.ACTIVE,
            created_by_user_id=user.id,
            updated_by_user_id=user.id,
        )
        session.add(client_session)
        await session.flush()
        workflow_run = WorkflowRun(
            tenant_id=tenant.id,
            session_id=client_session.id,
            workflow_id="W-A",
            workflow_slug="quick-diagnosis",
            status=WorkflowRunStatus.PLANNED,
            created_by_user_id=user.id,
            updated_by_user_id=user.id,
        )
        session.add(workflow_run)
        await session.flush()
        step = WorkflowStepRun(
            tenant_id=tenant.id,
            workflow_run_id=workflow_run.id,
            step_index=0,
            module_id="radimorphic",
            phase="scan",
            status=WorkflowStepRunStatus.PLANNED,
        )
        session.add(step)
        await session.commit()
        return tenant.id, user.id, client_session.id, workflow_run.id, step.id


def _headers(auth_service: AuthService, tenant_id: UUID, user_id: UUID) -> dict[str, str]:
    token = auth_service.issue_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        role=RoleName.THERAPIST,
        email="therapist@example.com",
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


async def _create_job(
    app: FastAPI,
    auth_service: AuthService,
    tenant_id: UUID,
    user_id: UUID,
    session_id: UUID,
    workflow_run_id: UUID,
    step_id: UUID,
) -> str:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/engines/radimorphic/jobs",
            headers=_headers(auth_service, tenant_id, user_id),
            json={
                "session_id": str(session_id),
                "workflow_run_id": str(workflow_run_id),
                "workflow_step_run_id": str(step_id),
            },
        )
    assert response.status_code == 200
    return str(response.json()["job_id"])


@pytest.mark.asyncio
async def test_create_job_returns_status(
    radimorphic_api: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, factory, auth_service = radimorphic_api
    tenant_id, user_id, session_id, workflow_run_id, step_id = await _seed_context(
        factory,
        slug="tenant-a",
    )

    job_id = await _create_job(
        app,
        auth_service,
        tenant_id,
        user_id,
        session_id,
        workflow_run_id,
        step_id,
    )

    assert UUID(job_id)


@pytest.mark.asyncio
async def test_get_job_status_returns_tenant_job(
    radimorphic_api: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, factory, auth_service = radimorphic_api
    tenant_id, user_id, session_id, workflow_run_id, step_id = await _seed_context(
        factory,
        slug="tenant-a",
    )
    job_id = await _create_job(
        app,
        auth_service,
        tenant_id,
        user_id,
        session_id,
        workflow_run_id,
        step_id,
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            f"/engines/radimorphic/jobs/{job_id}",
            headers=_headers(auth_service, tenant_id, user_id),
        )

    assert response.status_code == 200
    assert response.json()["job_status"] == "queued"


@pytest.mark.asyncio
async def test_result_client_projection_hides_raw_payload(
    radimorphic_api: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, factory, auth_service = radimorphic_api
    tenant_id, user_id, session_id, workflow_run_id, step_id = await _seed_context(
        factory,
        slug="tenant-a",
    )
    job_id = await _create_job(
        app,
        auth_service,
        tenant_id,
        user_id,
        session_id,
        workflow_run_id,
        step_id,
    )
    async with factory() as session:
        await RadiMorphicWorkerRuntimeService(
            session,
            engine=RadiMorphicEngine(seed=123),
        ).process_next_queued(tenant_id=tenant_id)
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            f"/engines/radimorphic/jobs/{job_id}/result?role=client",
            headers=_headers(auth_service, tenant_id, user_id),
        )

    body = response.json()
    assert response.status_code == 200
    assert body["role"] == "client"
    assert body["raw_debug_excluded"] is True
    assert "result_payload_json" not in body
    assert "metrics" not in body


@pytest.mark.asyncio
async def test_result_therapist_projection_contains_details(
    radimorphic_api: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, factory, auth_service = radimorphic_api
    tenant_id, user_id, session_id, workflow_run_id, step_id = await _seed_context(
        factory,
        slug="tenant-a",
    )
    job_id = await _create_job(
        app,
        auth_service,
        tenant_id,
        user_id,
        session_id,
        workflow_run_id,
        step_id,
    )
    async with factory() as session:
        await RadiMorphicWorkerRuntimeService(
            session,
            engine=RadiMorphicEngine(seed=123),
        ).process_next_queued(tenant_id=tenant_id)
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            f"/engines/radimorphic/jobs/{job_id}/result?role=therapist",
            headers=_headers(auth_service, tenant_id, user_id),
        )

    body = response.json()
    assert response.status_code == 200
    assert body["role"] == "therapist"
    assert body["metrics"]["quality_score"] >= 0
    assert body["top_resonances"]


@pytest.mark.asyncio
async def test_wrong_tenant_gets_404_for_result(
    radimorphic_api: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, factory, auth_service = radimorphic_api
    tenant_id, user_id, session_id, workflow_run_id, step_id = await _seed_context(
        factory,
        slug="tenant-a",
    )
    other_tenant_id, other_user_id, _other_session_id, _other_workflow_id, _other_step_id = (
        await _seed_context(factory, slug="tenant-b")
    )
    job_id = await _create_job(
        app,
        auth_service,
        tenant_id,
        user_id,
        session_id,
        workflow_run_id,
        step_id,
    )
    async with factory() as session:
        await RadiMorphicWorkerRuntimeService(
            session,
            engine=RadiMorphicEngine(seed=123),
        ).process_next_queued(tenant_id=tenant_id)
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            f"/engines/radimorphic/jobs/{job_id}/result",
            headers=_headers(auth_service, other_tenant_id, other_user_id),
        )

    assert response.status_code == 404
