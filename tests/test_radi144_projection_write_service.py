"""Radi144 ProjectionWriteService — W2b functional tests."""

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.base import Base
from app.db.session import make_async_engine
from app.models.client import ClientProfile
from app.models.engine import ModuleProjection, ModuleRun
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
from app.services.radi144 import Radi144ResultWriter
from app.services.radi144.projection_write_service import (
    ProjectionWriteError,
    ProjectionWriteResult,
    ProjectionWriteService,
)


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


async def _seed_and_write_result(
    factory: async_sessionmaker[AsyncSession],
) -> tuple[Tenant, UUID]:
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
            password_hash="not-used",
            status=UserStatus.ACTIVE,
            is_mfa_enabled=False,
        )
        session.add(user)
        await session.flush()
        client = ClientProfile(
            tenant_id=tenant.id,
            display_name="Client A",
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
        await session.flush()

        module_run_id = uuid4()
        result = Radi144Result(
            module_run_id=module_run_id,
            tenant_id=tenant.id,
            client_id=client.id,
            session_id=client_session.id,
            workflow_run_id=workflow_run.id,
            algorithm_version="radi144-domain-v1",
            manifest_version="1.0.0",
            compute_backend="simulation_disabled_until_engine_gate",
            coherence_scores={f"label_{i}": 0.1 for i in range(12)},
            biofield_map={f"label_{i}": 0.1 for i in range(12)},
            confidence=Radi144Confidence(score=0.75, data_quality=0.8, stability=0.9),
            synergy_seed=Radi144SynergySeed(
                top_labels=["label_0", "label_1", "label_2"],
                confidence_score=0.75,
                seed_checksum="1234567890abcdef",
            ),
            provenance=Radi144Provenance(
                algorithm_version="radi144-domain-v1",
                manifest_version="1.0.0",
                input_hash="1234567890abcdef",
                reference_matrix_version="radi144-reference-v1",
                compute_backend="simulation_disabled_until_engine_gate",
                duration_ms=0,
            ),
            retention=Radi144Retention(),
            client_projection=Radi144ClientProjectionPlaceholder(
                summary_label="Projection pending",
                quality_label="wellbeing quality pending",
            ),
        )
        await Radi144ResultWriter(session).persist_result(result=result, workflow_step_run_id=step.id)
        await session.commit()
        return tenant, module_run_id


@pytest.mark.asyncio
async def test_persist_projection_writes_client_and_therapist_rows(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant, module_run_id = await _seed_and_write_result(session_factory)

    async with session_factory() as session:
        write_result = await ProjectionWriteService(session).persist_projection(
            module_run_id=module_run_id, tenant_id=tenant.id
        )
        await session.commit()

    assert write_result.written == 2
    assert write_result.skipped == 0
    assert write_result.tenant_id == tenant.id
    assert write_result.module_run_id == module_run_id

    async with session_factory() as session:
        rows = list(
            await session.scalars(
                select(ModuleProjection).where(ModuleProjection.module_run_id == module_run_id)
            )
        )

    assert len(rows) == 2
    assert {r.role for r in rows} == {"client", "therapist"}
    for row in rows:
        assert row.raw_debug_excluded is True
        assert row.tenant_id == tenant.id


@pytest.mark.asyncio
async def test_persist_projection_is_idempotent(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant, module_run_id = await _seed_and_write_result(session_factory)

    async with session_factory() as session:
        first = await ProjectionWriteService(session).persist_projection(
            module_run_id=module_run_id, tenant_id=tenant.id
        )
        await session.commit()

    async with session_factory() as session:
        second = await ProjectionWriteService(session).persist_projection(
            module_run_id=module_run_id, tenant_id=tenant.id
        )
        await session.commit()

    assert first.written == 2 and first.skipped == 0
    assert second.written == 0 and second.skipped == 2


@pytest.mark.asyncio
async def test_persist_projection_rejects_wrong_tenant(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant, module_run_id = await _seed_and_write_result(session_factory)

    async with session_factory() as session:
        with pytest.raises(ProjectionWriteError) as exc_info:
            await ProjectionWriteService(session).persist_projection(
                module_run_id=module_run_id, tenant_id=uuid4()
            )

    assert exc_info.value.reason == "module_result_not_found_for_tenant"


@pytest.mark.asyncio
async def test_persist_projection_client_row_excludes_raw_debug(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant, module_run_id = await _seed_and_write_result(session_factory)

    async with session_factory() as session:
        await ProjectionWriteService(session).persist_projection(
            module_run_id=module_run_id, tenant_id=tenant.id
        )
        await session.commit()

    async with session_factory() as session:
        client_row = await session.scalar(
            select(ModuleProjection).where(
                ModuleProjection.module_run_id == module_run_id,
                ModuleProjection.role == "client",
            )
        )

    assert client_row is not None
    assert client_row.raw_debug_excluded is True
    assert client_row.projection_kind == "calm_summary"
    forbidden = {"raw_debug", "debug_json", "internal_state", "access_token", "password"}
    assert not (forbidden & set(client_row.projection_json.keys()))
