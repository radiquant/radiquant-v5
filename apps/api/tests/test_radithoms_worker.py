"""RadiThoms worker runtime tests."""

import sys
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

import app.models  # noqa: F401, E402
import app.models.radithoms  # noqa: F401, E402
from app.db.base import Base  # noqa: E402
from app.db.session import make_async_engine  # noqa: E402
from app.models.client import ClientProfile  # noqa: E402
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus  # noqa: E402
from app.models.radithoms import RadiThomsResult  # noqa: E402
from app.models.session import ClientSession, SessionGoal, SessionStatus  # noqa: E402
from app.models.workflow import (  # noqa: E402
    WorkflowRun,
    WorkflowRunStatus,
    WorkflowStepRun,
    WorkflowStepRunStatus,
)
from app.services.radithoms.engine import RadiThomsEngine  # noqa: E402
from app.services.radithoms.worker_runtime import (  # noqa: E402
    RadiThomsJobRecordService,
    RadiThomsWorkerRuntimeService,
)


@pytest_asyncio.fixture
async def radithoms_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    try:
        yield factory
    finally:
        await engine.dispose()


async def _seed_context(
    factory: async_sessionmaker[AsyncSession],
    *,
    slug: str = "tenant-a",
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
            module_id="radithoms",
            phase="analyze",
            status=WorkflowStepRunStatus.PLANNED,
        )
        session.add(step)
        await session.commit()
        return tenant.id, client_session.id, workflow_run.id, step.id, client.id


async def _create_job(
    factory: async_sessionmaker[AsyncSession],
    *,
    slug: str = "tenant-a",
) -> tuple[UUID, UUID]:
    tenant_id, session_id, workflow_run_id, step_id, _client_id = await _seed_context(
        factory,
        slug=slug,
    )
    async with factory() as session:
        module_run = await RadiThomsJobRecordService(session).create_or_get_job_record(
            tenant_id=tenant_id,
            session_id=session_id,
            workflow_run_id=workflow_run_id,
            workflow_step_run_id=step_id,
        )
        await session.commit()
        return tenant_id, module_run.id


@pytest.mark.asyncio
async def test_job_record_create_is_idempotent(
    radithoms_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id, session_id, workflow_run_id, step_id, _client_id = await _seed_context(
        radithoms_factory
    )

    async with radithoms_factory() as session:
        service = RadiThomsJobRecordService(session)
        first = await service.create_or_get_job_record(
            tenant_id=tenant_id,
            session_id=session_id,
            workflow_run_id=workflow_run_id,
            workflow_step_run_id=step_id,
        )
        second = await service.create_or_get_job_record(
            tenant_id=tenant_id,
            session_id=session_id,
            workflow_run_id=workflow_run_id,
            workflow_step_run_id=step_id,
        )

    assert first.id == second.id
    assert first.status == "queued"


@pytest.mark.asyncio
async def test_worker_processes_queued_job(
    radithoms_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id, module_run_id = await _create_job(radithoms_factory)

    async with radithoms_factory() as session:
        outcome = await RadiThomsWorkerRuntimeService(
            session,
            engine=RadiThomsEngine(seed=123),
        ).process_next_queued(tenant_id=tenant_id)
        await session.commit()

    assert outcome.status == "result_stored_cpu_safe"
    assert outcome.module_run_id == module_run_id
    assert outcome.result_written is True


@pytest.mark.asyncio
async def test_worker_status_check_reads_stored_job(
    radithoms_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id, module_run_id = await _create_job(radithoms_factory)

    async with radithoms_factory() as session:
        await RadiThomsWorkerRuntimeService(
            session,
            engine=RadiThomsEngine(seed=123),
        ).process_next_queued(tenant_id=tenant_id)
        stored = await RadiThomsJobRecordService(session).get_job_record(
            tenant_id=tenant_id,
            job_id=module_run_id,
        )

    assert stored is not None
    assert stored.status == "result_stored"


@pytest.mark.asyncio
async def test_worker_filters_by_tenant(
    radithoms_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id, _module_run_id = await _create_job(radithoms_factory)
    other_tenant_id, _session_id, _workflow_run_id, _step_id, _client_id = await _seed_context(
        radithoms_factory,
        slug="tenant-b",
    )

    async with radithoms_factory() as session:
        outcome = await RadiThomsWorkerRuntimeService(
            session,
            engine=RadiThomsEngine(seed=123),
        ).process_next_queued(tenant_id=other_tenant_id)

    assert outcome.status == "no_queued_job"
    assert outcome.tenant_id == other_tenant_id
    assert tenant_id != other_tenant_id


@pytest.mark.asyncio
async def test_worker_second_run_is_idempotent_no_duplicate_result(
    radithoms_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id, _module_run_id = await _create_job(radithoms_factory)

    async with radithoms_factory() as session:
        service = RadiThomsWorkerRuntimeService(session, engine=RadiThomsEngine(seed=123))
        first = await service.process_next_queued(tenant_id=tenant_id)
        second = await service.process_next_queued(tenant_id=tenant_id)
        result_count = await session.scalar(select(func.count()).select_from(RadiThomsResult))

    assert first.status == "result_stored_cpu_safe"
    assert second.status == "no_queued_job"
    assert result_count == 1
