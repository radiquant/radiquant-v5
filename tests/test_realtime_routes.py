"""Realtime API Gate tests.

This gate opens tenant-scoped SSE replay and fallback polling only. It does not
open Workflow UI, job tracker runtime, or engine execution.
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.routing import APIRoute
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db_session, make_async_engine
from app.main import create_app
from app.models.client import ClientConsent, ClientProfile, ConsentPurpose, ConsentStatus
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus
from app.schemas.event import EventEnvelopeCreate
from app.security.passwords import hash_password
from app.services.auth import AuthService, get_auth_service
from app.services.event_registry import EventWriter

FORBIDDEN_PAYLOAD_KEYS = {"raw_debug", "debug_json", "internal_state", "secret", "token", "access_token", "password"}


@pytest_asyncio.fixture
async def realtime_app() -> AsyncIterator[tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService]]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SECRET_KEY=SecretStr("realtime-test-secret-minimum-32-characters"),
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


async def _record_analysis_consent(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    tenant: Tenant,
    user: User,
    client: ClientProfile,
) -> None:
    async with session_factory() as session:
        session.add(
            ClientConsent(
                tenant_id=tenant.id,
                client_id=client.id,
                purpose=ConsentPurpose.ANALYSIS,
                status=ConsentStatus.GRANTED,
                consent_text_version="v1",
                recorded_by_user_id=user.id,
                granted_at=datetime.now(UTC),
            )
        )
        await session.commit()


def _headers(auth_service: AuthService, tenant: Tenant, user: User) -> dict[str, str]:
    token = auth_service.issue_access_token(user_id=user.id, tenant_id=tenant.id, role=RoleName.THERAPIST)
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant.id)}


def _session_payload(client: ClientProfile) -> dict[str, Any]:
    return {"client_id": str(client.id), "goal": {"title": "Wohlbefinden fokussieren", "description": "Ruhiger Start"}}


def _assert_no_forbidden_payload_keys(value: Any) -> None:
    if isinstance(value, dict):
        assert FORBIDDEN_PAYLOAD_KEYS.isdisjoint(value)
        for nested in value.values():
            _assert_no_forbidden_payload_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_forbidden_payload_keys(nested)


async def _append_workflow_event(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    tenant: Tenant,
    session_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> str:
    async with session_factory() as session:
        record = await EventWriter(session).append(
            EventEnvelopeCreate(
                event_type=event_type,
                occurred_at=datetime.now(UTC),
                tenant_id=tenant.id,
                session_id=session_id,
                correlation_id="corr-realtime-test",
                payload=payload,
            )
        )
        await session.commit()
        return str(record.event_id)


@pytest.mark.asyncio
async def test_list_session_events_replays_tenant_scoped_events_with_cursor(
    realtime_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = realtime_app
    tenant, user, client_profile = await _seed_client(session_factory, tenant_slug="tenant-a", email="a@example.com")
    await _record_analysis_consent(session_factory, tenant=tenant, user=user, client=client_profile)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created_session = await client.post("/sessions", json=_session_payload(client_profile), headers=_headers(auth_service, tenant, user))
    session_id = created_session.json()["id"]
    first_event_id = await _append_workflow_event(
        session_factory,
        tenant=tenant,
        session_id=session_id,
        event_type="workflow.created",
        payload={"workflow_id": "W-A"},
    )
    second_event_id = await _append_workflow_event(
        session_factory,
        tenant=tenant,
        session_id=session_id,
        event_type="workflow.started",
        payload={"workflow_id": "W-A", "status": "planned"},
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        listed = await client.get(f"/sessions/{session_id}/events", headers=_headers(auth_service, tenant, user))
        replayed = await client.get(
            f"/sessions/{session_id}/events",
            params={"after_event_id": first_event_id},
            headers=_headers(auth_service, tenant, user),
        )

    assert listed.status_code == 200
    body = listed.json()
    assert body["connection_state"] == "fallback"
    assert [item["event_id"] for item in body["items"]] == [first_event_id, second_event_id]
    assert body["next_cursor"] == second_event_id
    _assert_no_forbidden_payload_keys(body)

    assert replayed.status_code == 200
    assert [item["event_id"] for item in replayed.json()["items"]] == [second_event_id]


@pytest.mark.asyncio
async def test_session_events_reject_invalid_or_wrong_tenant_cursor(
    realtime_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = realtime_app
    tenant_a, user_a, client_a = await _seed_client(session_factory, tenant_slug="tenant-a", email="a@example.com")
    tenant_b, user_b, client_b = await _seed_client(session_factory, tenant_slug="tenant-b", email="b@example.com")
    await _record_analysis_consent(session_factory, tenant=tenant_a, user=user_a, client=client_a)
    await _record_analysis_consent(session_factory, tenant=tenant_b, user=user_b, client=client_b)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        session_a = await client.post("/sessions", json=_session_payload(client_a), headers=_headers(auth_service, tenant_a, user_a))
        session_b = await client.post("/sessions", json=_session_payload(client_b), headers=_headers(auth_service, tenant_b, user_b))
    wrong_tenant_event_id = await _append_workflow_event(
        session_factory,
        tenant=tenant_b,
        session_id=session_b.json()["id"],
        event_type="workflow.created",
        payload={"workflow_id": "W-A"},
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        invalid_cursor = await client.get(
            f"/sessions/{session_a.json()['id']}/events",
            params={"after_event_id": wrong_tenant_event_id},
            headers=_headers(auth_service, tenant_a, user_a),
        )
        wrong_tenant_session = await client.get(
            f"/sessions/{session_a.json()['id']}/events",
            headers=_headers(auth_service, tenant_b, user_b),
        )

    assert invalid_cursor.status_code == 422
    assert invalid_cursor.json()["detail"] == "Invalid replay cursor"
    assert wrong_tenant_session.status_code == 404


@pytest.mark.asyncio
async def test_stream_session_events_returns_sse_replay_batch(
    realtime_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = realtime_app
    tenant, user, client_profile = await _seed_client(session_factory, tenant_slug="tenant-a", email="a@example.com")
    await _record_analysis_consent(session_factory, tenant=tenant, user=user, client=client_profile)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created_session = await client.post("/sessions", json=_session_payload(client_profile), headers=_headers(auth_service, tenant, user))
    session_id = created_session.json()["id"]
    event_id = await _append_workflow_event(
        session_factory,
        tenant=tenant,
        session_id=session_id,
        event_type="workflow.created",
        payload={"workflow_id": "W-A"},
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        streamed = await client.get(f"/sessions/{session_id}/events/stream", headers=_headers(auth_service, tenant, user))

    assert streamed.status_code == 200
    assert streamed.headers["content-type"].startswith("text/event-stream")
    assert f"id: {event_id}" in streamed.text
    assert "event: workflow.created" in streamed.text
    assert '"workflow_id":"W-A"' in streamed.text


@pytest.mark.asyncio
@pytest.mark.parametrize("path_suffix", ["events", "events/stream"])
async def test_realtime_routes_require_authentication(
    realtime_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
    path_suffix: str,
) -> None:
    app, _session_factory, _auth_service = realtime_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/sessions/00000000-0000-0000-0000-000000000000/{path_suffix}")

    assert response.status_code == 401


def test_realtime_gate_does_not_open_job_engine_or_ui_routes(
    realtime_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, _session_factory, _auth_service = realtime_app
    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    forbidden_fragments = {"/jobs", "/engines", "/engine", "/modules", "/results", "/workflow-ui"}
    allowed_radi144_paths = {
        "/engines/radi144/jobs",
        "/engines/radi144/jobs/{job_id}",
        "/engines/radi144/jobs/{job_id}/result",
    }
    assert not [path for path in runtime_paths for fragment in forbidden_fragments if fragment in path and path not in allowed_radi144_paths]
