"""Radi144 Worker CPU Execution Wiring Gate tests."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.db.base import Base
from app.db.session import make_async_engine
from app.models.client import ClientConsent, ClientProfile, ConsentPurpose, ConsentStatus
from app.models.engine import ModuleProvenance, ModuleResult, ModuleRun
from app.models.event import EventRecord
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus
from app.models.session import ClientSession, SessionGoal, SessionStatus
from app.models.workflow import WorkflowRun, WorkflowRunStatus, WorkflowStepRun, WorkflowStepRunStatus
from app.security.passwords import hash_password
from app.services.radi144.job_records import Radi144JobRecordService
from app.services.radi144.worker_runtime import Radi144WorkerRuntimeService


@pytest_asyncio.fixture
async def wiring_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    _settings = Settings(DATABASE_URL="sqlite+aiosqlite:///:memory:", SECRET_KEY=SecretStr("worker-wiring-secret-minimum-32-characters"), ACCESS_TOKEN_TTL_MINUTES=5)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    try:
        yield factory
    finally:
        await engine.dispose()


async def _seed_queued_job_with_consent(factory: async_sessionmaker[AsyncSession]) -> ModuleRun:
    async with factory() as session:
        tenant = Tenant(slug="tenant-wiring", name="Tenant Wiring", status=TenantStatus.ACTIVE)
        role = Role(name=RoleName.THERAPIST, description="Therapist")
        session.add_all([tenant, role])
        await session.flush()
        user = User(tenant_id=tenant.id, role_id=role.id, email="wiring@example.com", display_name="Therapist", password_hash=hash_password("safe-password-123", iterations=1), status=UserStatus.ACTIVE, is_mfa_enabled=False)
        session.add(user)
        await session.flush()
        client = ClientProfile(tenant_id=tenant.id, display_name="Client Wiring", client_code="CW-1", created_by_user_id=user.id, updated_by_user_id=user.id)
        session.add(client)
        await session.flush()
        consent = ClientConsent(tenant_id=tenant.id, client_id=client.id, purpose=ConsentPurpose.ANALYSIS, status=ConsentStatus.GRANTED, consent_text_version="v1", recorded_by_user_id=user.id, granted_at=datetime.now(UTC))
        session.add(consent)
        await session.flush()
        goal = SessionGoal(tenant_id=tenant.id, client_id=client.id, title="Calm focus", description="Support a centered wellbeing session.", created_by_user_id=user.id)
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
        module_run = await Radi144JobRecordService(session).create_or_get_job_record(
            tenant_id=tenant.id,
            session_id=client_session.id,
            workflow_run_id=workflow_run.id,
            workflow_step_run_id=step.id,
        )
        await session.commit()
        return module_run


@pytest.mark.asyncio
async def test_worker_cpu_execution_stores_result_without_commit_inside_service(wiring_factory: async_sessionmaker[AsyncSession]) -> None:
    queued = await _seed_queued_job_with_consent(wiring_factory)

    async with wiring_factory() as session:
        outcome = await Radi144WorkerRuntimeService(session).process_next_queued(tenant_id=queued.tenant_id)
        await session.commit()

    assert outcome.status == "result_stored_cpu_safe"
    assert outcome.module_run_id == queued.id
    assert outcome.reason == "cpu_safe_result_stored"
    assert outcome.cpu_execution_enabled is True
    assert outcome.gpu_cuda_execution_enabled is False
    assert outcome.result_written is True

    async with wiring_factory() as session:
        module_run = await session.scalar(select(ModuleRun).where(ModuleRun.id == queued.id))
        module_result = await session.scalar(select(ModuleResult).where(ModuleResult.module_run_id == queued.id))
        provenance = await session.scalar(select(ModuleProvenance).where(ModuleProvenance.module_run_id == queued.id))
        events = (await session.scalars(select(EventRecord).where(EventRecord.resource_id == str(queued.id)).order_by(EventRecord.occurred_at))).all()

    assert module_run is not None
    assert module_run.status == "result_stored"
    assert module_result is not None
    assert module_result.result_payload_json["compute_backend"] == "cpu"
    assert module_result.raw_debug_allowed is False
    assert module_result.projection_status == "pending_projection_builder"
    assert provenance is not None
    assert provenance.compute_backend == "cpu"
    assert [event.event_type for event in events] == ["job.running", "module.radi144.started", "module.radi144.completed", "job.done"]
    assert all(event.tenant_id == queued.tenant_id for event in events)
    assert all(event.payload_json["compute_backend"] == "cpu" for event in events)
    assert "raw_debug" not in str([event.payload_json for event in events])


@pytest.mark.asyncio
async def test_worker_cpu_execution_is_idempotently_consumed(wiring_factory: async_sessionmaker[AsyncSession]) -> None:
    queued = await _seed_queued_job_with_consent(wiring_factory)

    async with wiring_factory() as session:
        first = await Radi144WorkerRuntimeService(session).process_next_queued(tenant_id=queued.tenant_id)
        await session.commit()
    async with wiring_factory() as session:
        second = await Radi144WorkerRuntimeService(session).process_next_queued(tenant_id=queued.tenant_id)

    assert first.status == "result_stored_cpu_safe"
    assert second.status == "no_queued_job"
    assert second.result_written is False
