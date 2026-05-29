"""Tenant-scoped session API tests."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
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
from app.models.session import ClientSession, SessionStatus
from app.security.passwords import hash_password
from app.services.auth import AuthService, get_auth_service

FORBIDDEN_SESSION_KEYS = {
    "workflow_id",
    "workflow_step",
    "engine",
    "engine_id",
    "module",
    "module_id",
    "result",
    "realtime",
    "raw_debug",
    "debug_json",
    "internal_state",
    "metadata_json",
}


@pytest_asyncio.fixture
async def session_app() -> AsyncIterator[tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService]]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SECRET_KEY=SecretStr("session-test-secret-minimum-32-characters"),
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
    status: ConsentStatus = ConsentStatus.GRANTED,
    expires_at: datetime | None = None,
) -> None:
    async with session_factory() as session:
        now = datetime.now(UTC)
        session.add(
            ClientConsent(
                tenant_id=tenant.id,
                client_id=client.id,
                purpose=ConsentPurpose.ANALYSIS,
                status=status,
                consent_text_version="v1",
                recorded_by_user_id=user.id,
                granted_at=now,
                revoked_at=now if status == ConsentStatus.REVOKED else None,
                expires_at=expires_at,
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
        assert FORBIDDEN_SESSION_KEYS.isdisjoint(value)
        for nested in value.values():
            _assert_no_forbidden_keys(nested)
    elif isinstance(value, list):
        for item in value:
            _assert_no_forbidden_keys(item)


@pytest.mark.asyncio
async def test_create_session_requires_active_analysis_consent_and_audits(
    session_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = session_app
    tenant, user, client_profile = await _seed_client(session_factory, tenant_slug="tenant-a", email="a@example.com")
    await _record_analysis_consent(session_factory, tenant=tenant, user=user, client=client_profile)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/sessions", json=_session_payload(client_profile), headers=_headers(auth_service, tenant, user))

    assert response.status_code == 201
    body = response.json()
    assert body["tenant_id"] == str(tenant.id)
    assert body["client_id"] == str(client_profile.id)
    assert body["status"] == SessionStatus.ACTIVE.value
    assert body["goal"]["title"] == "Wohlbefinden fokussieren"
    _assert_no_forbidden_keys(body)

    async with session_factory() as session:
        audit = (await session.execute(select(AuditLog))).scalar_one()
    assert audit.action == AuditAction.SESSION_START
    assert audit.reason == "session_started"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("consent_status", "expires_delta"),
    [(None, None), (ConsentStatus.REVOKED, None), (ConsentStatus.GRANTED, timedelta(seconds=-1))],
)
async def test_create_session_rejects_missing_revoked_or_expired_consent(
    session_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
    consent_status: ConsentStatus | None,
    expires_delta: timedelta | None,
) -> None:
    app, session_factory, auth_service = session_app
    tenant, user, client_profile = await _seed_client(session_factory, tenant_slug="tenant-a", email="a@example.com")
    if consent_status is not None:
        await _record_analysis_consent(
            session_factory,
            tenant=tenant,
            user=user,
            client=client_profile,
            status=consent_status,
            expires_at=datetime.now(UTC) + expires_delta if expires_delta is not None else None,
        )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/sessions", json=_session_payload(client_profile), headers=_headers(auth_service, tenant, user))

    assert response.status_code == 403
    assert response.json()["detail"] == "Consent required"


@pytest.mark.asyncio
async def test_create_session_wrong_tenant_client_returns_not_found(
    session_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = session_app
    tenant_a, user_a, client_a = await _seed_client(session_factory, tenant_slug="tenant-a", email="a@example.com")
    tenant_b, user_b, _client_b = await _seed_client(session_factory, tenant_slug="tenant-b", email="b@example.com")
    await _record_analysis_consent(session_factory, tenant=tenant_a, user=user_a, client=client_a)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/sessions", json=_session_payload(client_a), headers=_headers(auth_service, tenant_b, user_b))

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_and_get_sessions_are_tenant_scoped(
    session_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = session_app
    tenant_a, user_a, client_a = await _seed_client(session_factory, tenant_slug="tenant-a", email="a@example.com")
    tenant_b, user_b, client_b = await _seed_client(session_factory, tenant_slug="tenant-b", email="b@example.com")
    await _record_analysis_consent(session_factory, tenant=tenant_a, user=user_a, client=client_a)
    await _record_analysis_consent(session_factory, tenant=tenant_b, user=user_b, client=client_b)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created_a = await client.post("/sessions", json=_session_payload(client_a), headers=_headers(auth_service, tenant_a, user_a))
        created_b = await client.post("/sessions", json=_session_payload(client_b), headers=_headers(auth_service, tenant_b, user_b))
        listed = await client.get("/sessions", headers=_headers(auth_service, tenant_a, user_a))
        same_tenant = await client.get(f"/sessions/{created_a.json()['id']}", headers=_headers(auth_service, tenant_a, user_a))
        wrong_tenant = await client.get(f"/sessions/{created_a.json()['id']}", headers=_headers(auth_service, tenant_b, user_b))

    assert created_a.status_code == 201
    assert created_b.status_code == 201
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [created_a.json()["id"]]
    assert same_tenant.status_code == 200
    assert wrong_tenant.status_code == 404


@pytest.mark.asyncio
async def test_update_session_status_closes_active_session(
    session_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = session_app
    tenant, user, client_profile = await _seed_client(session_factory, tenant_slug="tenant-a", email="a@example.com")
    await _record_analysis_consent(session_factory, tenant=tenant, user=user, client=client_profile)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post("/sessions", json=_session_payload(client_profile), headers=_headers(auth_service, tenant, user))
        updated = await client.patch(
            f"/sessions/{created.json()['id']}/status",
            json={"status": "completed"},
            headers=_headers(auth_service, tenant, user),
        )
        repeated = await client.patch(
            f"/sessions/{created.json()['id']}/status",
            json={"status": "cancelled"},
            headers=_headers(auth_service, tenant, user),
        )

    assert updated.status_code == 200
    assert updated.json()["status"] == SessionStatus.COMPLETED.value
    assert updated.json()["ended_at"] is not None
    assert repeated.status_code == 409

    async with session_factory() as session:
        audits = (await session.execute(select(AuditLog).order_by(AuditLog.created_at))).scalars().all()
    assert [audit.reason for audit in audits] == ["session_started", "session_status_updated"]


@pytest.mark.asyncio
@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer invalid"}])
async def test_session_routes_require_authentication(
    session_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
    headers: dict[str, str],
) -> None:
    app, _session_factory, _auth_service = session_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/sessions", headers=headers)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_session_routes_require_matching_tenant_header(
    session_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = session_app
    tenant_a, user_a, _client_a = await _seed_client(session_factory, tenant_slug="tenant-a", email="a@example.com")
    tenant_b, _user_b, _client_b = await _seed_client(session_factory, tenant_slug="tenant-b", email="b@example.com")
    token = auth_service.issue_access_token(user_id=user_a.id, tenant_id=tenant_a.id, role=RoleName.THERAPIST)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        missing = await client.get("/sessions", headers={"Authorization": f"Bearer {token}"})
        mismatch = await client.get(
            "/sessions",
            headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_b.id)},
        )

    assert missing.status_code == 403
    assert mismatch.status_code == 403


@pytest.mark.asyncio
async def test_session_tables_do_not_contain_workflow_or_engine_columns() -> None:
    forbidden = {"workflow_id", "workflow_step", "engine_id", "module_id", "module", "result", "realtime"}
    assert forbidden.isdisjoint(ClientSession.__table__.columns.keys())
