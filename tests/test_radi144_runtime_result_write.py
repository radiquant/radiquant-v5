"""Radi144 Runtime Result Write Gate tests."""

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.base import Base
from app.db.session import make_async_engine
from app.models.client import ClientProfile
from app.models.engine import ModuleProvenance, ModuleResult, ModuleRun
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
from app.services.radi144 import Radi144ResultWriteError, Radi144ResultWriter


@pytest_asyncio.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    try:
        yield factory
    finally:
        await engine.dispose()


async def _seed_workflow_step(factory: async_sessionmaker[AsyncSession]) -> tuple[Tenant, WorkflowStepRun, ClientSession, WorkflowRun]:
    async with factory() as session:
        tenant = Tenant(slug="tenant-a", name="Tenant A", status=TenantStatus.ACTIVE)
        role = Role(name=RoleName.THERAPIST, description="Therapist")
        session.add_all([tenant, role])
        await session.flush()
        user = User(
            tenant_id=tenant.id,
            role_id=role.id,
            email="a@example.com",
            display_name="Therapist",
            password_hash="not-used-in-result-writer-test",
            status=UserStatus.ACTIVE,
            is_mfa_enabled=False,
        )
        session.add(user)
        await session.flush()
        client = ClientProfile(tenant_id=tenant.id, display_name="Client A", created_by_user_id=user.id, updated_by_user_id=user.id)
        session.add(client)
        await session.flush()
        goal = SessionGoal(tenant_id=tenant.id, client_id=client.id, title="Wellbeing focus", description="", created_by_user_id=user.id)
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
            module_id="radi144",
            phase="diagnose",
            status=WorkflowStepRunStatus.PLANNED,
        )
        session.add(step)
        await session.commit()
        return tenant, step, client_session, workflow_run


def _result(*, tenant: Tenant, step: WorkflowStepRun, client_session: ClientSession, workflow_run: WorkflowRun) -> Radi144Result:
    return Radi144Result(
        module_run_id=uuid4(),
        tenant_id=tenant.id,
        client_id=client_session.client_id,
        session_id=client_session.id,
        workflow_run_id=workflow_run.id,
        algorithm_version="radi144-domain-v1",
        manifest_version="1.0.0",
        compute_backend="simulation_disabled_until_engine_gate",
        coherence_scores={f"label_{index}": 0.1 for index in range(12)},
        biofield_map={f"label_{index}": 0.1 for index in range(12)},
        confidence=Radi144Confidence(score=0.5, data_quality=0.6, stability=0.7),
        synergy_seed=Radi144SynergySeed(top_labels=["label_0", "label_1", "label_2"], confidence_score=0.5, seed_checksum="1234567890abcdef"),
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


@pytest.mark.asyncio
async def test_result_writer_persists_module_run_result_and_provenance(session_factory: async_sessionmaker[AsyncSession]) -> None:
    tenant, step, client_session, workflow_run = await _seed_workflow_step(session_factory)
    result = _result(tenant=tenant, step=step, client_session=client_session, workflow_run=workflow_run)

    async with session_factory() as session:
        module_run = await Radi144ResultWriter(session).persist_result(result=result, workflow_step_run_id=step.id)
        await session.commit()

        stored_run = await session.scalar(select(ModuleRun).where(ModuleRun.id == module_run.id))
        stored_result = await session.scalar(select(ModuleResult).where(ModuleResult.module_run_id == module_run.id))
        stored_provenance = await session.scalar(select(ModuleProvenance).where(ModuleProvenance.module_run_id == module_run.id))

    assert stored_run is not None
    assert stored_run.tenant_id == tenant.id
    assert stored_run.status == "result_stored"
    assert stored_result is not None
    assert stored_result.retention_json["raw_debug_allowed"] is False
    assert stored_result.projection_status == "pending_projection_builder"
    assert stored_provenance is not None
    assert stored_provenance.input_hash == "1234567890abcdef"


@pytest.mark.asyncio
async def test_result_writer_rejects_wrong_tenant_workflow_step(session_factory: async_sessionmaker[AsyncSession]) -> None:
    tenant, step, client_session, workflow_run = await _seed_workflow_step(session_factory)
    result = _result(tenant=tenant, step=step, client_session=client_session, workflow_run=workflow_run)
    result = result.model_copy(update={"tenant_id": uuid4()})

    async with session_factory() as session:
        with pytest.raises(Radi144ResultWriteError) as exc_info:
            await Radi144ResultWriter(session).persist_result(result=result, workflow_step_run_id=step.id)

    assert exc_info.value.reason == "workflow_step_not_found_for_tenant"


@pytest.mark.asyncio
async def test_result_writer_rejects_forbidden_debug_payload(session_factory: async_sessionmaker[AsyncSession]) -> None:
    tenant, step, client_session, workflow_run = await _seed_workflow_step(session_factory)
    result = _result(tenant=tenant, step=step, client_session=client_session, workflow_run=workflow_run)
    result = result.model_copy(update={"coherence_scores": {**result.coherence_scores, "raw_debug": 0.1}})

    async with session_factory() as session:
        with pytest.raises(Radi144ResultWriteError) as exc_info:
            await Radi144ResultWriter(session).persist_result(result=result, workflow_step_run_id=step.id)

    assert exc_info.value.reason == "forbidden_result_key:raw_debug"
