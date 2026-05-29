"""Identity login/logout API tests for the security core."""

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db_session, make_async_engine
from app.main import create_app
from app.models.audit import AuditAction, AuditLog
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus
from app.security.passwords import hash_password
from app.services.auth import AuthService, get_auth_service


@pytest_asyncio.fixture
async def identity_app() -> AsyncIterator[tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService]]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SECRET_KEY="identity-test-secret-minimum-32-characters",
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


async def _seed_identity(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    tenant_slug: str = "tenant-a",
    email: str = "therapist@example.com",
    password: str = "safe-password-123",
    user_status: UserStatus = UserStatus.ACTIVE,
) -> tuple[Tenant, Role, User]:
    async with session_factory() as session:
        tenant = Tenant(slug=tenant_slug, name="Tenant A", status=TenantStatus.ACTIVE)
        role = Role(name=RoleName.THERAPIST, description="Therapist")
        session.add_all([tenant, role])
        await session.flush()
        user = User(
            tenant_id=tenant.id,
            role_id=role.id,
            email=email,
            display_name="Therapist Example",
            password_hash=hash_password(password, iterations=1),
            status=user_status,
            is_mfa_enabled=False,
        )
        session.add(user)
        await session.commit()
        return tenant, role, user


@pytest.mark.asyncio
async def test_login_success_returns_token_and_audits_event(
    identity_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, _auth_service = identity_app
    tenant, _role, user = await _seed_identity(session_factory)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={
                "tenant_slug": tenant.slug,
                "email": user.email,
                "password": "safe-password-123",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["tenant_id"] == str(tenant.id)
    assert body["user_id"] == str(user.id)
    assert body["role"] == RoleName.THERAPIST.value
    assert body["access_token"]

    async with session_factory() as session:
        audit = (await session.execute(select(AuditLog))).scalar_one()
    assert audit.tenant_id == tenant.id
    assert audit.actor_user_id == user.id
    assert audit.action == AuditAction.LOGIN_SECURITY_EVENT
    assert audit.resource_type == "identity.login"
    assert audit.reason == "login_success"


@pytest.mark.asyncio
async def test_login_rejects_wrong_password_and_audits_denial(
    identity_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, _auth_service = identity_app
    tenant, _role, user = await _seed_identity(session_factory)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={"tenant_slug": tenant.slug, "email": user.email, "password": "wrong-password"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
    async with session_factory() as session:
        audit = (await session.execute(select(AuditLog))).scalar_one()
    assert audit.tenant_id == tenant.id
    assert audit.actor_user_id == user.id
    assert audit.reason == "login_failed"
    assert audit.metadata_json == {"outcome": "denied"}


@pytest.mark.asyncio
async def test_login_rejects_disabled_user(
    identity_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, _auth_service = identity_app
    tenant, _role, user = await _seed_identity(session_factory, user_status=UserStatus.DISABLED)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={
                "tenant_slug": tenant.slug,
                "email": user.email,
                "password": "safe-password-123",
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_tenant_does_not_disclose_existence(
    identity_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, _session_factory, _auth_service = identity_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={
                "tenant_slug": "unknown-tenant",
                "email": "therapist@example.com",
                "password": "safe-password-123",
            },
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_logout_requires_authentication(
    identity_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, _session_factory, _auth_service = identity_app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/auth/logout")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_records_audit_event(
    identity_app: tuple[FastAPI, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    app, session_factory, auth_service = identity_app
    tenant, _role, user = await _seed_identity(session_factory)
    token = auth_service.issue_access_token(user_id=user.id, tenant_id=tenant.id, role=RoleName.THERAPIST)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    async with session_factory() as session:
        audits = (await session.execute(select(AuditLog).order_by(AuditLog.created_at))).scalars().all()
    assert len(audits) == 1
    assert audits[0].tenant_id == tenant.id
    assert audits[0].actor_user_id == user.id
    assert audits[0].resource_type == "identity.logout"
    assert audits[0].reason == "logout"
