"""Workflow API Gate tests.

These tests verify manifest-derived planning only. Engine execution, realtime,
results, and UI progress remain outside this gate.
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

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
from app.models.audit import AuditAction, AuditLog
from app.models.client import ClientConsent, ClientProfile, ConsentPurpose, ConsentStatus
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus
from app.models.session import SessionStatus
from app.models.workflow import WorkflowRun, WorkflowRunStatus, WorkflowStepRun
from app.security.passwords import hash_password
from app.services.auth import AuthService, get_auth_service

FORBIDDEN_WORKFLOW_KEYS = {
    "engine_run_id",
    "module_result",
    "result",
    "raw_debug",
    "debug_json",
    "internal_state",
    "realtime",
    "progress",
}


@pytest_asyncio.fixture
async def workflow_app() -> AsyncIterator[tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService]]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SECRET_KEY=SecretStr("workflow-test-secret-minimum-32-characters"),
        ACCESS_TOKEN_TTL_MINUTES=5,
    )
    auth_service = AuthService(settings=settings)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    app = create_app()

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_auth_service] = lambda: auth_service

    try:
        yield app, session_factory, auth_service
    finally:
        await engine.dispose()


async def _seed_client(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    tenant_slug: str,
    email: str,
) -> tuple[Tenant, User, ClientProfile]:
    async with session_factory() as session:
        tenant = Tenant(slug=tenant_slug, name=tenant_slug.title(), status=TenantStatus.ACTIVE)
        role = await session.scalar(select(Role).where(Role.name == RoleName.THERAPIST))
        if role is None:
            role = Role(name=RoleName.THERAPIST, description="Therapist")
            session.add(role)
        session.add(tenant)
        await session.flush()
        user = User(
            tenant_id=tenant.id,
            role_id=role.id,
            email=email,
            display_name=email,
            password_hash=hash_password("safe-password-123", iterations=1),
            status=UserStatus.ACTIVE,
            is_mfa_enabled=False,
        )
        session.add(user)
        await session.flush()
        client = ClientProfile(
            tenant_id=tenant.id,
            display_name=f"Client {tenant_slug}",
            created_by_user_id=user.id,
            updated_by_user_id=user.id,
        )
        session.add(client)
        await session.commit()
        return tenant, user, client


async def _record_consents(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    tenant: Tenant,
    user: User,
    client: ClientProfile,
    purposes: list[ConsentPurpose],
) -> None:
    async with session_factory() as session:
        now = datetime.now(UTC)
        for purpose in purposes:
            session.add(
                ClientConsent(
                    tenant_id=tenant.id,
                    client_id=client.id,
                    purpose=purpose,
                    status=ConsentStatus.GRANTED,
                    consent_text_version="v1",
                    recorded_by_user_id=user.id,
                    granted_at=now,
                )
            )
        await session.commit()


def _headers(auth_service: AuthService, tenant: Tenant, user: User) -> dict[str, str]:
    token = auth_service.issue_access_token(user_id=user.id, tenant_id=tenant.id, role=RoleName.THERAPIST)
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant.id)}


def _session_payload(client: ClientProfile) -> dict[str, Any]:
    return {"client_id": str(client.id), "goal": {"title": "Wohlbefinden fokussieren", "description": "Ruhiger Start"}}


def _assert_no_forbidden_keys(value: Any) -> None:
    if isinstance(value, dict):
        assert FORBIDDEN_WORKFLOW_KEYS.isdisjoint(value)
        for nested in value.values():
            _assert_no_forbidden_keys(nested)
    elif isinstance(value, list):
        for item in value:
            _assert_no_forbidden_keys(item)


@pytest.mark.asyncio
async def test_create_workflow_run_plans_manifest_steps_and_audits(
    workflow_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = workflow_app
    tenant, user, client_profile = await _seed_client(session_factory, tenant_slug="tenant-a", email="a@example.com")
    await _record_consents(
        session_factory,
        tenant=tenant,
        user=user,
        client=client_profile,
        purposes=[ConsentPurpose.ANALYSIS],
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created_session = await client.post("/sessions", json=_session_payload(client_profile), headers=_headers(auth_service, tenant, user))
        created_workflow = await client.post(
            f"/sessions/{created_session.json()['id']}/workflow-runs",
            json={"workflow_id": "W-A"},
            headers=_headers(auth_service, tenant, user),
        )

    assert created_workflow.status_code == 201
    body = created_workflow.json()
    assert body["tenant_id"] == str(tenant.id)
    assert body["session_id"] == created_session.json()["id"]
    assert body["workflow_id"] == "W-A"
    assert body["workflow_slug"] == "quick-diagnosis"
    assert body["status"] == WorkflowRunStatus.PLANNED.value
    assert [step["module_id"] for step in body["steps"]] == ["radi144", "radiworks"]
    assert [step["step_index"] for step in body["steps"]] == [0, 1]
    _assert_no_forbidden_keys(body)

    async with session_factory() as session:
        workflow_run = (await session.execute(select(WorkflowRun))).scalar_one()
        steps = (await session.execute(select(WorkflowStepRun).order_by(WorkflowStepRun.step_index))).scalars().all()
        audits = (await session.execute(select(AuditLog).order_by(AuditLog.created_at))).scalars().all()

    assert workflow_run.workflow_id == "W-A"
    assert [step.module_id for step in steps] == ["radi144", "radiworks"]
    assert [audit.reason for audit in audits] == ["session_started", "workflow_run_planned"]
    assert audits[-1].action == AuditAction.WORKFLOW_PLAN


@pytest.mark.asyncio
async def test_workflow_run_requires_all_manifest_consents(
    workflow_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = workflow_app
    tenant, user, client_profile = await _seed_client(session_factory, tenant_slug="tenant-a", email="a@example.com")
    await _record_consents(
        session_factory,
        tenant=tenant,
        user=user,
        client=client_profile,
        purposes=[ConsentPurpose.ANALYSIS],
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created_session = await client.post("/sessions", json=_session_payload(client_profile), headers=_headers(auth_service, tenant, user))
        denied = await client.post(
            f"/sessions/{created_session.json()['id']}/workflow-runs",
            json={"workflow_id": "W-B"},
            headers=_headers(auth_service, tenant, user),
        )

    assert denied.status_code == 403
    assert denied.json()["detail"] == "Consent required"


@pytest.mark.asyncio
async def test_workflow_run_rejects_later_gate_workflow(
    workflow_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = workflow_app
    tenant, user, client_profile = await _seed_client(session_factory, tenant_slug="tenant-a", email="a@example.com")
    await _record_consents(
        session_factory,
        tenant=tenant,
        user=user,
        client=client_profile,
        purposes=[ConsentPurpose.ANALYSIS],
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created_session = await client.post("/sessions", json=_session_payload(client_profile), headers=_headers(auth_service, tenant, user))
        rejected = await client.post(
            f"/sessions/{created_session.json()['id']}/workflow-runs",
            json={"workflow_id": "W-C"},
            headers=_headers(auth_service, tenant, user),
        )

    assert rejected.status_code == 409
    assert rejected.json()["detail"] == "Workflow requires a later gate"


@pytest.mark.asyncio
async def test_list_workflow_runs_is_tenant_scoped(
    workflow_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = workflow_app
    tenant_a, user_a, client_a = await _seed_client(session_factory, tenant_slug="tenant-a", email="a@example.com")
    tenant_b, user_b, client_b = await _seed_client(session_factory, tenant_slug="tenant-b", email="b@example.com")
    await _record_consents(session_factory, tenant=tenant_a, user=user_a, client=client_a, purposes=[ConsentPurpose.ANALYSIS])
    await _record_consents(session_factory, tenant=tenant_b, user=user_b, client=client_b, purposes=[ConsentPurpose.ANALYSIS])

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        session_a = await client.post("/sessions", json=_session_payload(client_a), headers=_headers(auth_service, tenant_a, user_a))
        session_b = await client.post("/sessions", json=_session_payload(client_b), headers=_headers(auth_service, tenant_b, user_b))
        workflow_a = await client.post(
            f"/sessions/{session_a.json()['id']}/workflow-runs",
            json={"workflow_id": "W-A"},
            headers=_headers(auth_service, tenant_a, user_a),
        )
        await client.post(
            f"/sessions/{session_b.json()['id']}/workflow-runs",
            json={"workflow_id": "W-A"},
            headers=_headers(auth_service, tenant_b, user_b),
        )
        listed = await client.get(f"/sessions/{session_a.json()['id']}/workflow-runs", headers=_headers(auth_service, tenant_a, user_a))
        wrong_tenant = await client.get(f"/sessions/{session_a.json()['id']}/workflow-runs", headers=_headers(auth_service, tenant_b, user_b))

    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [workflow_a.json()["id"]]
    assert wrong_tenant.status_code == 404


@pytest.mark.asyncio
async def test_workflow_routes_require_authentication(
    workflow_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, _session_factory, _auth_service = workflow_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/sessions/00000000-0000-0000-0000-000000000000/workflow-runs")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_workflow_tables_do_not_contain_engine_realtime_or_result_columns() -> None:
    forbidden = {"engine_run_id", "module_result", "result", "raw_debug", "debug_json", "realtime", "progress"}
    assert forbidden.isdisjoint(WorkflowRun.__table__.columns.keys())
    assert forbidden.isdisjoint(WorkflowStepRun.__table__.columns.keys())
