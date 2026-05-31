"""Harmonization job lifecycle tests."""

import sys
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

import app.models  # noqa: F401, E402
import app.models.harmonization  # noqa: F401, E402
from app.core.config import Settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db_session, make_async_engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.audit import AuditLog  # noqa: E402
from app.models.client import ClientProfile  # noqa: E402
from app.models.harmonization import HarmonizationJob, HarmonizationPlan  # noqa: E402
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus  # noqa: E402
from app.models.session import ClientSession, SessionGoal, SessionStatus  # noqa: E402
from app.services.auth import AuthService, get_auth_service  # noqa: E402
from app.services.harmonization_worker import HarmonizationWorkerService  # noqa: E402


@pytest_asyncio.fixture
async def harmonization_job_api() -> AsyncIterator[
    tuple[object, async_sessionmaker[AsyncSession], AuthService]
]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    auth_service = AuthService(
        settings=Settings(
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
            SECRET_KEY=SecretStr("harmonization-job-secret-minimum-32-chars"),
            ACCESS_TOKEN_TTL_MINUTES=5,
        )
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    api = create_app()

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    api.dependency_overrides[get_db_session] = override_db_session
    api.dependency_overrides[get_auth_service] = lambda: auth_service

    try:
        yield api, factory, auth_service
    finally:
        await engine.dispose()


async def _seed_session(
    factory: async_sessionmaker[AsyncSession],
    *,
    slug: str = "tenant-job-a",
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


async def _create_plan(
    factory: async_sessionmaker[AsyncSession],
    *,
    tenant_id: UUID,
    user_id: UUID,
    session_id: UUID,
    status: str = "approved",
) -> UUID:
    async with factory() as session:
        plan = HarmonizationPlan(
            session_id=session_id,
            tenant_id=tenant_id,
            status=status,
            plan_payload_json={"mode": "balance"},
            created_by_user_id=user_id,
            approved_by_user_id=user_id if status == "approved" else None,
            approved_at=datetime.now(UTC) if status == "approved" else None,
        )
        session.add(plan)
        await session.commit()
        return plan.id


def _headers(auth_service: AuthService, tenant_id: UUID, user_id: UUID) -> dict[str, str]:
    token = auth_service.issue_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        role=RoleName.THERAPIST,
        email="therapist@example.com",
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


async def _start_job(
    api: object,
    auth_service: AuthService,
    tenant_id: UUID,
    user_id: UUID,
    plan_id: UUID,
) -> dict[str, object]:
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as client:
        response = await client.post(
            f"/sessions/harmonization/jobs?plan_id={plan_id}",
            headers=_headers(auth_service, tenant_id, user_id),
        )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_start_job_requires_approved_plan(
    harmonization_job_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    _api, factory, _auth_service = harmonization_job_api
    tenant_id, user_id, session_id = await _seed_session(factory)
    plan_id = await _create_plan(
        factory,
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
        status="draft",
    )

    async with factory() as session:
        with pytest.raises(HTTPException) as exc_info:
            await HarmonizationWorkerService().start(plan_id, tenant_id, session)

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_start_job_creates_running_job(
    harmonization_job_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    api, factory, auth_service = harmonization_job_api
    tenant_id, user_id, session_id = await _seed_session(factory)
    plan_id = await _create_plan(
        factory,
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
    )

    body = await _start_job(api, auth_service, tenant_id, user_id, plan_id)

    assert body["status"] == "running"
    assert body["plan_id"] == str(plan_id)
    assert body["tenant_id"] == str(tenant_id)
    assert body["hardware_ack"] is False
    assert body["started_at"] is not None


@pytest.mark.asyncio
async def test_pause_running_job(
    harmonization_job_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    api, factory, auth_service = harmonization_job_api
    tenant_id, user_id, session_id = await _seed_session(factory)
    plan_id = await _create_plan(
        factory,
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
    )
    started = await _start_job(api, auth_service, tenant_id, user_id, plan_id)

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as client:
        response = await client.patch(
            f"/sessions/harmonization/jobs/{started['id']}/pause",
            headers=_headers(auth_service, tenant_id, user_id),
        )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "paused"
    assert body["paused_at"] is not None


@pytest.mark.asyncio
async def test_resume_paused_job(
    harmonization_job_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    api, factory, auth_service = harmonization_job_api
    tenant_id, user_id, session_id = await _seed_session(factory)
    plan_id = await _create_plan(
        factory,
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
    )
    started = await _start_job(api, auth_service, tenant_id, user_id, plan_id)

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as client:
        pause = await client.patch(
            f"/sessions/harmonization/jobs/{started['id']}/pause",
            headers=_headers(auth_service, tenant_id, user_id),
        )
        resume = await client.patch(
            f"/sessions/harmonization/jobs/{started['id']}/resume",
            headers=_headers(auth_service, tenant_id, user_id),
        )

    assert pause.status_code == 200
    assert resume.status_code == 200
    assert resume.json()["status"] == "running"


@pytest.mark.asyncio
async def test_stop_job_sets_cancelled(
    harmonization_job_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    api, factory, auth_service = harmonization_job_api
    tenant_id, user_id, session_id = await _seed_session(factory)
    plan_id = await _create_plan(
        factory,
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
    )
    started = await _start_job(api, auth_service, tenant_id, user_id, plan_id)

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as client:
        response = await client.patch(
            f"/sessions/harmonization/jobs/{started['id']}/stop",
            headers=_headers(auth_service, tenant_id, user_id),
        )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "cancelled"
    assert body["completed_at"] is not None

    async with factory() as session:
        actions = list(
            (
                await session.execute(
                    text("select action from audit_logs where resource_id = :resource_id"),
                    {"resource_id": str(started["id"])},
                )
            )
            .scalars()
            .all()
        )

    assert "harmonization_job_cancelled" in actions


@pytest.mark.asyncio
async def test_hardware_fallback_on_timeout(
    harmonization_job_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _api, factory, _auth_service = harmonization_job_api
    tenant_id, user_id, session_id = await _seed_session(factory)
    plan_id = await _create_plan(
        factory,
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
    )
    service = HarmonizationWorkerService()

    async def timeout_ack(job: HarmonizationJob) -> bool:
        raise TimeoutError

    monkeypatch.setattr(service, "_wait_for_hardware_ack", timeout_ack)

    async with factory() as session:
        job = await service.start(plan_id, tenant_id, session)

    assert job.status == "running"
    assert job.hardware_ack is False

    async with factory() as session:
        metadata_json = await session.scalar(
            select(AuditLog.metadata_json).where(AuditLog.resource_id == str(job.id))
        )

    assert metadata_json is not None
    assert metadata_json["hardware_fallback"] is True


@pytest.mark.asyncio
async def test_job_tenant_isolation(
    harmonization_job_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    _api, factory, _auth_service = harmonization_job_api
    tenant_id, user_id, session_id = await _seed_session(factory, slug="tenant-job-a")
    other_tenant_id, _other_user_id, _other_session_id = await _seed_session(
        factory,
        slug="tenant-job-b",
    )
    plan_id = await _create_plan(
        factory,
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
    )

    async with factory() as session:
        with pytest.raises(HTTPException) as exc_info:
            await HarmonizationWorkerService().start(plan_id, other_tenant_id, session)

    assert exc_info.value.status_code == 404
