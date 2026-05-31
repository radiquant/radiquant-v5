"""SynergyService tests."""

import sys
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

import app.models  # noqa: F401, E402
from app.core.config import Settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db_session, make_async_engine  # noqa: E402
from app.models.client import ClientProfile  # noqa: E402
from app.models.engine import ModuleResult, ModuleRun  # noqa: E402
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus  # noqa: E402
from app.models.session import ClientSession, SessionGoal, SessionStatus  # noqa: E402
from app.models.workflow import (  # noqa: E402
    WorkflowRun,
    WorkflowRunStatus,
    WorkflowStepRun,
    WorkflowStepRunStatus,
)
from app.routes.sessions import router as sessions_router  # noqa: E402
from app.services.auth import AuthService, get_auth_service  # noqa: E402
from app.services.synergy_service import SynergyService  # noqa: E402


@pytest_asyncio.fixture
async def synergy_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def synergy_api() -> AsyncIterator[
    tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService]
]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    auth_service = AuthService(
        settings=Settings(
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
            SECRET_KEY=SecretStr("synergy-api-secret-minimum-32-characters"),
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
    app.include_router(sessions_router)

    try:
        yield app, factory, auth_service
    finally:
        await engine.dispose()


async def _seed_session(
    factory: async_sessionmaker[AsyncSession],
    *,
    slug: str = "tenant-a",
) -> tuple[UUID, UUID, UUID]:
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
            description="",
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
        await session.commit()
        return tenant.id, user.id, client_session.id


async def _add_module_result(
    factory: async_sessionmaker[AsyncSession],
    *,
    tenant_id: UUID,
    session_id: UUID,
    module_id: str,
    score: float,
    step_index: int,
) -> UUID:
    async with factory() as session:
        workflow_run = await session.scalar(
            select(WorkflowRun).where(
                WorkflowRun.tenant_id == tenant_id,
                WorkflowRun.session_id == session_id,
            )
        )
        if workflow_run is None:
            workflow_run = WorkflowRun(
                tenant_id=tenant_id,
                session_id=session_id,
                workflow_id="W-A",
                workflow_slug="quick-diagnosis",
                status=WorkflowRunStatus.PLANNED,
            )
            session.add(workflow_run)
            await session.flush()
        step = WorkflowStepRun(
            tenant_id=tenant_id,
            workflow_run_id=workflow_run.id,
            step_index=step_index,
            module_id=module_id,
            phase="analyze",
            status=WorkflowStepRunStatus.PLANNED,
        )
        session.add(step)
        await session.flush()
        module_run = ModuleRun(
            tenant_id=tenant_id,
            session_id=session_id,
            workflow_run_id=workflow_run.id,
            workflow_step_run_id=step.id,
            module_id=module_id,
            phase="analyze",
            status="result_stored",
            schema_id="radi144_result_v1",
            job_contract_schema_id=f"{module_id}_job_v1",
        )
        session.add(module_run)
        await session.flush()
        session.add(
            ModuleResult(
                tenant_id=tenant_id,
                module_run_id=module_run.id,
                schema_id="radi144_result_v1",
                result_payload_json={"score": score},
                retention_json={"policy": "test"},
                projection_status="pending_projection_builder",
                raw_debug_allowed=False,
                client_projection_required=True,
            )
        )
        await session.commit()
        return module_run.id


def _headers(auth_service: AuthService, tenant_id: UUID, user_id: UUID) -> dict[str, str]:
    token = auth_service.issue_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        role=RoleName.THERAPIST,
        email="therapist@example.com",
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


@pytest.mark.asyncio
async def test_synergy_empty_session_raises_404(
    synergy_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id, _user_id, session_id = await _seed_session(synergy_factory)

    async with synergy_factory() as session:
        with pytest.raises(HTTPException) as exc_info:
            await SynergyService().compute(
                session_id=session_id,
                tenant_id=tenant_id,
                db=session,
            )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_synergy_confidence_calculation(
    synergy_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id, _user_id, session_id = await _seed_session(synergy_factory)
    await _add_module_result(
        synergy_factory,
        tenant_id=tenant_id,
        session_id=session_id,
        module_id="radi144",
        score=0.6,
        step_index=0,
    )
    await _add_module_result(
        synergy_factory,
        tenant_id=tenant_id,
        session_id=session_id,
        module_id="radiworks",
        score=0.7,
        step_index=1,
    )

    async with synergy_factory() as session:
        result = await SynergyService().compute(
            session_id=session_id,
            tenant_id=tenant_id,
            db=session,
        )

    assert result.modules_complete == ["radi144", "radiworks"]
    assert result.modules_pending == ["radimorphic", "radiblohm", "radithoms", "radicopen"]
    assert result.confidence == pytest.approx(2 / 6)


@pytest.mark.asyncio
async def test_synergy_conflict_detection(
    synergy_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id, _user_id, session_id = await _seed_session(synergy_factory)
    await _add_module_result(
        synergy_factory,
        tenant_id=tenant_id,
        session_id=session_id,
        module_id="radi144",
        score=0.05,
        step_index=0,
    )
    await _add_module_result(
        synergy_factory,
        tenant_id=tenant_id,
        session_id=session_id,
        module_id="radiworks",
        score=0.95,
        step_index=1,
    )

    async with synergy_factory() as session:
        result = await SynergyService().compute(
            session_id=session_id,
            tenant_id=tenant_id,
            db=session,
        )

    assert len(result.conflicts) == 1
    assert result.conflicts[0].conflict_type == "score_polarity"
    assert result.conflicts[0].severity == "high"


@pytest.mark.asyncio
async def test_synergy_tenant_isolation(
    synergy_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id, _user_id, session_id = await _seed_session(synergy_factory, slug="tenant-a")
    other_tenant_id, _other_user_id, _other_session_id = await _seed_session(
        synergy_factory,
        slug="tenant-b",
    )
    await _add_module_result(
        synergy_factory,
        tenant_id=tenant_id,
        session_id=session_id,
        module_id="radi144",
        score=0.6,
        step_index=0,
    )

    async with synergy_factory() as session:
        with pytest.raises(HTTPException) as exc_info:
            await SynergyService().compute(
                session_id=session_id,
                tenant_id=other_tenant_id,
                db=session,
            )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_synergy_endpoint_returns_result(
    synergy_api: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, factory, auth_service = synergy_api
    tenant_id, user_id, session_id = await _seed_session(factory)
    await _add_module_result(
        factory,
        tenant_id=tenant_id,
        session_id=session_id,
        module_id="radi144",
        score=0.6,
        step_index=0,
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            f"/sessions/{session_id}/synergy",
            headers=_headers(auth_service, tenant_id, user_id),
        )

    body = response.json()
    assert response.status_code == 200
    assert body["session_id"] == str(session_id)
    assert body["tenant_id"] == str(tenant_id)
    assert body["modules_complete"] == ["radi144"]
