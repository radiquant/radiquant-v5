"""Tenant-scoped client profile and consent API tests."""

from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi import FastAPI
from pydantic import SecretStr
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db_session, make_async_engine
from app.main import create_app
from app.models.audit import AuditAction, AuditLog
from app.models.client import ClientConsent, ClientProfile, ClientStatus, ConsentPurpose
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus
from app.security.passwords import hash_password
from app.services.auth import AuthService, get_auth_service

FORBIDDEN_RESPONSE_KEYS = {"raw_debug", "debug_json", "internal_state", "metadata_json", "password_hash", "access_token"}


@pytest_asyncio.fixture
async def client_app() -> AsyncIterator[tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService]]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SECRET_KEY=SecretStr("client-test-secret-minimum-32-characters"),
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


async def _seed_user(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    tenant_slug: str,
    email: str,
) -> tuple[Tenant, User]:
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
        await session.commit()
        return tenant, user


def _headers(auth_service: AuthService, tenant: Tenant, user: User) -> dict[str, str]:
    token = auth_service.issue_access_token(user_id=user.id, tenant_id=tenant.id, role=RoleName.THERAPIST)
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant.id)}


def _assert_no_forbidden_keys(value: Any) -> None:
    if isinstance(value, dict):
        assert FORBIDDEN_RESPONSE_KEYS.isdisjoint(value)
        for nested in value.values():
            _assert_no_forbidden_keys(nested)
    elif isinstance(value, list):
        for item in value:
            _assert_no_forbidden_keys(item)


@pytest.mark.asyncio
async def test_create_client_profile_returns_safe_projection_and_audits(
    client_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = client_app
    tenant, user = await _seed_user(session_factory, tenant_slug="tenant-a", email="a@example.com")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/clients",
            json={"display_name": "Mensch A", "client_code": "A-001"},
            headers=_headers(auth_service, tenant, user),
        )

    assert response.status_code == 201
    body = response.json()
    assert body["tenant_id"] == str(tenant.id)
    assert body["display_name"] == "Mensch A"
    assert body["client_code"] == "A-001"
    assert body["status"] == ClientStatus.ACTIVE.value
    _assert_no_forbidden_keys(body)

    async with session_factory() as session:
        audit = (await session.execute(select(AuditLog))).scalar_one()
    assert audit.tenant_id == tenant.id
    assert audit.actor_user_id == user.id
    assert audit.action == AuditAction.CLIENT_CREATE_UPDATE_DELETE
    assert audit.resource_type == "client_profile"
    assert audit.reason == "client_created"


@pytest.mark.asyncio
async def test_list_client_profiles_is_tenant_scoped(
    client_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = client_app
    tenant_a, user_a = await _seed_user(session_factory, tenant_slug="tenant-a", email="a@example.com")
    tenant_b, user_b = await _seed_user(session_factory, tenant_slug="tenant-b", email="b@example.com")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/clients", json={"display_name": "A"}, headers=_headers(auth_service, tenant_a, user_a))
        await client.post("/clients", json={"display_name": "B"}, headers=_headers(auth_service, tenant_b, user_b))
        response = await client.get("/clients", headers=_headers(auth_service, tenant_a, user_a))

    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert [item["display_name"] for item in body["items"]] == ["A"]
    _assert_no_forbidden_keys(body)


@pytest.mark.asyncio
async def test_detail_and_update_wrong_tenant_return_not_found(
    client_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = client_app
    tenant_a, user_a = await _seed_user(session_factory, tenant_slug="tenant-a", email="a@example.com")
    tenant_b, user_b = await _seed_user(session_factory, tenant_slug="tenant-b", email="b@example.com")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post("/clients", json={"display_name": "A"}, headers=_headers(auth_service, tenant_a, user_a))
        client_id = created.json()["id"]
        same_tenant = await client.get(f"/clients/{client_id}", headers=_headers(auth_service, tenant_a, user_a))
        wrong_tenant_get = await client.get(f"/clients/{client_id}", headers=_headers(auth_service, tenant_b, user_b))
        wrong_tenant_patch = await client.patch(
            f"/clients/{client_id}",
            json={"display_name": "Nope"},
            headers=_headers(auth_service, tenant_b, user_b),
        )
        updated = await client.patch(
            f"/clients/{client_id}",
            json={"display_name": "A Updated", "status": "archived"},
            headers=_headers(auth_service, tenant_a, user_a),
        )

    assert same_tenant.status_code == 200
    assert wrong_tenant_get.status_code == 404
    assert wrong_tenant_patch.status_code == 404
    assert updated.status_code == 200
    assert updated.json()["display_name"] == "A Updated"
    assert updated.json()["status"] == ClientStatus.ARCHIVED.value


@pytest.mark.asyncio
async def test_record_and_list_client_consent_audits_event(
    client_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = client_app
    tenant, user = await _seed_user(session_factory, tenant_slug="tenant-a", email="a@example.com")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post("/clients", json={"display_name": "A"}, headers=_headers(auth_service, tenant, user))
        client_id = created.json()["id"]
        consent = await client.post(
            f"/clients/{client_id}/consents",
            json={"purpose": "analysis", "consent_text_version": "v1"},
            headers=_headers(auth_service, tenant, user),
        )
        listed = await client.get(f"/clients/{client_id}/consents", headers=_headers(auth_service, tenant, user))

    assert consent.status_code == 201
    consent_body = consent.json()
    assert consent_body["tenant_id"] == str(tenant.id)
    assert consent_body["client_id"] == client_id
    assert consent_body["purpose"] == ConsentPurpose.ANALYSIS.value
    _assert_no_forbidden_keys(consent_body)
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1

    async with session_factory() as session:
        consent_rows = (await session.execute(select(ClientConsent))).scalars().all()
        audits = (await session.execute(select(AuditLog))).scalars().all()
    assert len(consent_rows) == 1
    assert {audit.action for audit in audits} == {AuditAction.CLIENT_CREATE_UPDATE_DELETE, AuditAction.CONSENT_CHANGE}


@pytest.mark.asyncio
async def test_wrong_tenant_consent_write_returns_not_found(
    client_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = client_app
    tenant_a, user_a = await _seed_user(session_factory, tenant_slug="tenant-a", email="a@example.com")
    tenant_b, user_b = await _seed_user(session_factory, tenant_slug="tenant-b", email="b@example.com")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post("/clients", json={"display_name": "A"}, headers=_headers(auth_service, tenant_a, user_a))
        response = await client.post(
            f"/clients/{created.json()['id']}/consents",
            json={"purpose": "analysis", "consent_text_version": "v1"},
            headers=_headers(auth_service, tenant_b, user_b),
        )

    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer invalid"}])
async def test_client_routes_require_authentication(
    client_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
    headers: dict[str, str],
) -> None:
    app, _session_factory, _auth_service = client_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/clients", headers=headers)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_client_routes_require_tenant_header(
    client_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = client_app
    tenant, user = await _seed_user(session_factory, tenant_slug="tenant-a", email="a@example.com")
    token = auth_service.issue_access_token(user_id=user.id, tenant_id=tenant.id, role=RoleName.THERAPIST)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/clients", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_client_routes_reject_mismatched_tenant_header(
    client_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = client_app
    tenant_a, user_a = await _seed_user(session_factory, tenant_slug="tenant-a", email="a@example.com")
    tenant_b, _user_b = await _seed_user(session_factory, tenant_slug="tenant-b", email="b@example.com")
    token = auth_service.issue_access_token(user_id=user_a.id, tenant_id=tenant_a.id, role=RoleName.THERAPIST)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/clients",
            headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_b.id)},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_client_profile_response_excludes_raw_debug_fields(
    client_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = client_app
    tenant, user = await _seed_user(session_factory, tenant_slug="tenant-a", email="a@example.com")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/clients", json={"display_name": "A"}, headers=_headers(auth_service, tenant, user))

    assert response.status_code == 201
    _assert_no_forbidden_keys(response.json())
    assert set(response.json()) == {"id", "tenant_id", "display_name", "client_code", "status", "created_at", "updated_at"}


@pytest.mark.asyncio
async def test_client_models_are_tenant_scoped_in_metadata() -> None:
    assert "tenant_id" in ClientProfile.__table__.columns
    assert "tenant_id" in ClientConsent.__table__.columns
