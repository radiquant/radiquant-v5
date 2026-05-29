"""Event Schema Gate tests.

This gate validates and stores event envelopes only. Realtime, replay endpoints,
job tracking, and engine progress remain blocked.
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db_session, make_async_engine
from app.main import create_app
from app.models.event import EventRecord
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus
from app.schemas.event import EventEnvelopeCreate
from app.security.passwords import hash_password
from app.services.auth import AuthService, get_auth_service
from app.services.event_registry import EventRegistryService, EventSchemaError, EventWriter

FORBIDDEN_PAYLOAD_KEYS = {"raw_debug", "debug_json", "internal_state", "secret", "token", "access_token", "password"}


@pytest_asyncio.fixture
async def event_app() -> AsyncIterator[tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService]]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SECRET_KEY=SecretStr("event-test-secret-minimum-32-characters"),
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


async def _seed_tenant_user(session_factory: async_sessionmaker[AsyncSession]) -> tuple[Tenant, User]:
    async with session_factory() as session:
        tenant = Tenant(slug="tenant-a", name="Tenant A", status=TenantStatus.ACTIVE)
        role = Role(name=RoleName.THERAPIST, description="Therapist")
        session.add_all([tenant, role])
        await session.flush()
        user = User(
            tenant_id=tenant.id,
            role_id=role.id,
            email="a@example.com",
            display_name="a@example.com",
            password_hash=hash_password("safe-password-123", iterations=1),
            status=UserStatus.ACTIVE,
            is_mfa_enabled=False,
        )
        session.add(user)
        await session.commit()
        return tenant, user


def _assert_no_forbidden_payload_keys(value: Any) -> None:
    if isinstance(value, dict):
        assert FORBIDDEN_PAYLOAD_KEYS.isdisjoint(value)
        for nested in value.values():
            _assert_no_forbidden_payload_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_forbidden_payload_keys(nested)


@pytest.mark.asyncio
async def test_event_writer_validates_and_persists_workflow_event(
    event_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    _app, session_factory, _auth_service = event_app
    tenant, _user = await _seed_tenant_user(session_factory)
    session_id = uuid4()
    event_id = uuid4()

    async with session_factory() as session:
        record = await EventWriter(session).append(
            EventEnvelopeCreate(
                event_id=event_id,
                event_type="workflow.created",
                occurred_at=datetime.now(UTC),
                tenant_id=tenant.id,
                correlation_id="corr-event-schema",
                session_id=session_id,
                resource_type="workflow_run",
                resource_id=str(uuid4()),
                payload={"workflow_id": "W-A", "status": "planned"},
            )
        )
        await session.commit()
        persisted = await session.scalar(select(EventRecord).where(EventRecord.id == record.id))

    assert persisted is not None
    assert persisted.event_id == event_id
    assert persisted.tenant_id == tenant.id
    assert persisted.event_type == "workflow.created"
    assert persisted.session_id == session_id
    assert persisted.payload_json == {"workflow_id": "W-A", "status": "planned"}
    _assert_no_forbidden_payload_keys(persisted.payload_json)


def test_event_registry_rejects_unknown_event_type() -> None:
    service = EventRegistryService()
    with pytest.raises(EventSchemaError) as exc_info:
        service.validate_envelope(
            EventEnvelopeCreate(
                event_type="unknown.event",
                occurred_at=datetime.now(UTC),
                tenant_id=uuid4(),
                correlation_id="corr-event-schema",
                payload={},
            )
        )
    assert exc_info.value.reason == "unknown_event_type"


@pytest.mark.parametrize("forbidden_key", sorted(FORBIDDEN_PAYLOAD_KEYS))
def test_event_registry_rejects_forbidden_payload_keys(forbidden_key: str) -> None:
    with pytest.raises(EventSchemaError) as exc_info:
        EventRegistryService().validate_envelope(
            EventEnvelopeCreate(
                event_type="job.queued",
                occurred_at=datetime.now(UTC),
                tenant_id=uuid4(),
                correlation_id="corr-event-schema",
                payload={"nested": {forbidden_key: "blocked"}},
            )
        )
    assert exc_info.value.reason == f"forbidden_payload_key:{forbidden_key}"


def test_event_registry_requires_workflow_context_ids() -> None:
    service = EventRegistryService()
    with pytest.raises(EventSchemaError) as workflow_exc:
        service.validate_envelope(
            EventEnvelopeCreate(
                event_type="workflow.started",
                occurred_at=datetime.now(UTC),
                tenant_id=uuid4(),
                correlation_id="corr-event-schema",
            )
        )
    assert workflow_exc.value.reason == "session_id_required"

    with pytest.raises(EventSchemaError) as step_exc:
        service.validate_envelope(
            EventEnvelopeCreate(
                event_type="step.started",
                occurred_at=datetime.now(UTC),
                tenant_id=uuid4(),
                session_id=uuid4(),
                correlation_id="corr-event-schema",
            )
        )
    assert step_exc.value.reason == "workflow_run_id_required"

    with pytest.raises(EventSchemaError) as substep_exc:
        service.validate_envelope(
            EventEnvelopeCreate(
                event_type="substep.started",
                occurred_at=datetime.now(UTC),
                tenant_id=uuid4(),
                session_id=uuid4(),
                workflow_run_id=uuid4(),
                correlation_id="corr-event-schema",
            )
        )
    assert substep_exc.value.reason == "workflow_step_run_id_required"


def test_event_schema_gate_does_not_open_job_engine_or_ui_routes(
    event_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, _session_factory, _auth_service = event_app
    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    forbidden_fragments = {"/jobs", "/engines", "/engine", "/modules", "/results", "/workflow-ui"}
    allowed_radi144_paths = {
        "/engines/radi144/jobs",
        "/engines/radi144/jobs/{job_id}",
        "/engines/radi144/jobs/{job_id}/result",
    }
    assert not [path for path in runtime_paths for fragment in forbidden_fragments if fragment in path and path not in allowed_radi144_paths]


@pytest.mark.asyncio
async def test_event_table_has_no_realtime_transport_columns() -> None:
    forbidden = {"sse", "websocket", "connection_state", "replay_cursor", "stream_id"}
    assert forbidden.isdisjoint(EventRecord.__table__.columns.keys())
