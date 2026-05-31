"""Report service and claim linter tests."""

import sys
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi import HTTPException
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
from app.main import create_app  # noqa: E402
from app.models.client import ClientProfile  # noqa: E402
from app.models.engine import ModuleProjection, ModuleResult, ModuleRun  # noqa: E402
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus  # noqa: E402
from app.models.session import ClientSession, SessionGoal, SessionStatus  # noqa: E402
from app.models.workflow import (  # noqa: E402
    WorkflowRun,
    WorkflowRunStatus,
    WorkflowStepRun,
    WorkflowStepRunStatus,
)
from app.services.auth import AuthService, get_auth_service  # noqa: E402
from app.services.claim_linter import ClaimLinterService, ClaimViolationError  # noqa: E402
from app.services.report_service import ReportService  # noqa: E402


@pytest_asyncio.fixture
async def report_api() -> AsyncIterator[
    tuple[object, async_sessionmaker[AsyncSession], AuthService]
]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    auth_service = AuthService(
        settings=Settings(
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
            SECRET_KEY=SecretStr("report-secret-minimum-32-characters"),
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
    slug: str = "tenant-report-a",
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


async def _seed_module_report_data(
    factory: async_sessionmaker[AsyncSession],
    *,
    tenant_id: UUID,
    user_id: UUID,
    session_id: UUID,
    module_id: str = "radi144",
    client_payload: dict[str, object] | None = None,
    therapist_payload: dict[str, object] | None = None,
    score: float = 0.2,
) -> UUID:
    async with factory() as session:
        workflow_run = WorkflowRun(
            tenant_id=tenant_id,
            session_id=session_id,
            workflow_id="W-A",
            workflow_slug="quick-diagnosis",
            status=WorkflowRunStatus.PLANNED,
            created_by_user_id=user_id,
            updated_by_user_id=user_id,
        )
        session.add(workflow_run)
        await session.flush()
        step = WorkflowStepRun(
            tenant_id=tenant_id,
            workflow_run_id=workflow_run.id,
            step_index=0,
            module_id=module_id,
            phase="diagnose",
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
            phase="diagnose",
            status="result_stored",
            schema_id="radi144_result_v1",
            job_contract_schema_id="radi144_job_v1",
        )
        session.add(module_run)
        await session.flush()
        session.add(
            ModuleResult(
                tenant_id=tenant_id,
                module_run_id=module_run.id,
                schema_id="radi144_result_v1",
                result_payload_json={"score": score, "raw_payload_secret": "never expose"},
                retention_json={},
                projection_status="pending_projection_builder",
                raw_debug_allowed=False,
                client_projection_required=True,
            )
        )
        session.add(
            ModuleProjection(
                tenant_id=tenant_id,
                module_run_id=module_run.id,
                role="client",
                projection_kind="calm_summary",
                projection_json=client_payload
                or {
                    "summary_label": "Calm focus",
                    "quality_label": "balanced wellbeing signal",
                    "raw_debug": "raw_payload_secret",
                    "result_payload_json": {"secret": "never expose"},
                    "module_run_id": str(module_run.id),
                },
                raw_debug_excluded=True,
            )
        )
        session.add(
            ModuleProjection(
                tenant_id=tenant_id,
                module_run_id=module_run.id,
                role="therapist",
                projection_kind="therapist_summary",
                projection_json=therapist_payload
                or {
                    "summary_label": "Therapist review",
                    "quality_label": "cross-module review ready",
                },
                raw_debug_excluded=True,
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


def test_claim_linter_passes_clean_text() -> None:
    ClaimLinterService().lint("Unterstuetzende Wellbeing-Zusammenfassung ohne Heilversprechen.")


def test_claim_linter_detects_heilt() -> None:
    with pytest.raises(ClaimViolationError) as exc_info:
        ClaimLinterService().lint("Diese Analyse heilt Beschwerden.")

    assert "heilt" in exc_info.value.violations


def test_claim_linter_detects_medizinisch() -> None:
    with pytest.raises(ClaimViolationError) as exc_info:
        ClaimLinterService().lint("Dies ist keine medizinisch freigegebene Aussage.")

    assert "medizinisch" in exc_info.value.violations


def test_claim_linter_case_insensitive() -> None:
    with pytest.raises(ClaimViolationError) as exc_info:
        ClaimLinterService().lint("GARANTIERT eine Wirkung.")

    assert "GARANTIERT" in exc_info.value.violations


@pytest.mark.asyncio
async def test_client_report_excludes_raw_payload(
    report_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    _api, factory, _auth_service = report_api
    tenant_id, user_id, session_id = await _seed_session(factory)
    await _seed_module_report_data(
        factory,
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
    )

    async with factory() as session:
        report = await ReportService().build_client_report(session_id, tenant_id, session)

    assert "Calm focus" in report.summary
    assert "raw_payload_secret" not in report.summary
    assert "never expose" not in report.summary
    assert report.modules == ["radi144"]


@pytest.mark.asyncio
async def test_client_report_tenant_scoped(
    report_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    _api, factory, _auth_service = report_api
    tenant_id, user_id, session_id = await _seed_session(factory, slug="tenant-report-a")
    other_tenant_id, other_user_id, _other_session_id = await _seed_session(
        factory,
        slug="tenant-report-b",
    )
    await _seed_module_report_data(
        factory,
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
    )

    async with factory() as session:
        with pytest.raises(HTTPException) as exc_info:
            await ReportService().build_client_report(session_id, other_tenant_id, session)

    assert exc_info.value.status_code == 404
    assert other_user_id != user_id


@pytest.mark.asyncio
async def test_therapist_appendix_includes_synergy(
    report_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    _api, factory, _auth_service = report_api
    tenant_id, user_id, session_id = await _seed_session(factory)
    await _seed_module_report_data(
        factory,
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
    )

    async with factory() as session:
        appendix = await ReportService().build_therapist_appendix(session_id, tenant_id, session)

    assert appendix.role == "therapist"
    assert "radi144" in appendix.modules
    assert "radi144" in appendix.synergy.modules_complete
    assert appendix.synergy.tenant_id == tenant_id


@pytest.mark.asyncio
async def test_report_endpoint_client_role(
    report_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    api, factory, auth_service = report_api
    tenant_id, user_id, session_id = await _seed_session(factory)
    await _seed_module_report_data(
        factory,
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
    )

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as client:
        response = await client.get(
            f"/sessions/{session_id}/report?role=client",
            headers=_headers(auth_service, tenant_id, user_id),
        )

    body = response.json()
    assert response.status_code == 200
    assert body["role"] == "client"
    assert body["tenant_id"] == str(tenant_id)
    assert body["modules"] == ["radi144"]
