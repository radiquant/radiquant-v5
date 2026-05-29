"""Radi144 Worker Job Gate Decision tests."""

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db_session, make_async_engine
from app.main import create_app
from app.models.client import ClientProfile
from app.models.engine import ModuleRun
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus
from app.models.session import ClientSession, SessionGoal, SessionStatus
from app.models.workflow import WorkflowRun, WorkflowRunStatus, WorkflowStepRun, WorkflowStepRunStatus
from app.security.passwords import hash_password
from app.services.auth import AuthService, get_auth_service


@pytest_asyncio.fixture
async def worker_job_app() -> AsyncIterator[tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService]]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    settings = Settings(DATABASE_URL="sqlite+aiosqlite:///:memory:", SECRET_KEY=SecretStr("worker-job-secret-minimum-32-characters"), ACCESS_TOKEN_TTL_MINUTES=5)
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


async def _seed_step(factory: async_sessionmaker[AsyncSession]) -> tuple[Tenant, User, ClientSession, WorkflowRun, WorkflowStepRun]:
    async with factory() as session:
        tenant = Tenant(slug="tenant-job", name="Tenant Job", status=TenantStatus.ACTIVE)
        role = Role(name=RoleName.THERAPIST, description="Therapist")
        session.add_all([tenant, role])
        await session.flush()
        user = User(tenant_id=tenant.id, role_id=role.id, email="job@example.com", display_name="Therapist", password_hash=hash_password("safe-password-123", iterations=1), status=UserStatus.ACTIVE, is_mfa_enabled=False)
        session.add(user)
        await session.flush()
        client = ClientProfile(tenant_id=tenant.id, display_name="Client Job", created_by_user_id=user.id, updated_by_user_id=user.id)
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
        await session.commit()
        return tenant, user, client_session, workflow_run, step


def _payload(client_session: ClientSession, workflow_run: WorkflowRun, step: WorkflowStepRun) -> dict[str, str]:
    return {
        "session_id": str(client_session.id),
        "workflow_run_id": str(workflow_run.id),
        "workflow_step_run_id": str(step.id),
        "idempotency_key": "job-key-123",
    }


@pytest.mark.asyncio
async def test_post_creates_queued_job_record(worker_job_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService]) -> None:
    app, factory, auth_service = worker_job_app
    tenant, user, client_session, workflow_run, step = await _seed_step(factory)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/engines/radi144/jobs", json=_payload(client_session, workflow_run, step), headers=_headers(auth_service, tenant, user))

    assert response.status_code == 200
    body = response.json()
    assert body["route_status"] == "job_record_created_no_worker_runtime"
    assert body["job_status"] == "queued"
    assert body["worker_jobs_enabled"] is False
    assert body["engine_execution_enabled"] is False
    job_id = UUID(body["job_id"])
    async with factory() as session:
        module_run = await session.scalar(select(ModuleRun).where(ModuleRun.id == job_id, ModuleRun.tenant_id == tenant.id))
    assert module_run is not None
    assert module_run.status == "queued"
    assert module_run.workflow_step_run_id == step.id


@pytest.mark.asyncio
async def test_post_is_idempotent_for_workflow_step(worker_job_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService]) -> None:
    app, _factory, auth_service = worker_job_app
    tenant, user, client_session, workflow_run, step = await _seed_step(_factory)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        first = await client.post("/engines/radi144/jobs", json=_payload(client_session, workflow_run, step), headers=_headers(auth_service, tenant, user))
        second = await client.post("/engines/radi144/jobs", json=_payload(client_session, workflow_run, step), headers=_headers(auth_service, tenant, user))

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["job_id"] == second.json()["job_id"]


@pytest.mark.asyncio
async def test_job_status_is_tenant_scoped(worker_job_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService]) -> None:
    app, factory, auth_service = worker_job_app
    tenant, user, client_session, workflow_run, step = await _seed_step(factory)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post("/engines/radi144/jobs", json=_payload(client_session, workflow_run, step), headers=_headers(auth_service, tenant, user))
        other_tenant = Tenant(id=uuid4(), slug="other", name="Other", status=TenantStatus.ACTIVE)
        other_user = User(id=uuid4(), tenant_id=other_tenant.id, role_id=user.role_id, email="other@example.com", display_name="Other", password_hash="unused", status=UserStatus.ACTIVE, is_mfa_enabled=False)
        response = await client.get(f"/engines/radi144/jobs/{created.json()['job_id']}", headers=_headers(auth_service, other_tenant, other_user))

    assert response.status_code == 404
