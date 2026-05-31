"""Admin route tests."""

import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

import app.models  # noqa: F401, E402
from app.core.config import Settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db_session, make_async_engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.audit import AuditAction, AuditLog  # noqa: E402
from app.models.client import ClientProfile  # noqa: E402
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus  # noqa: E402
from app.models.session import ClientSession, SessionGoal, SessionStatus  # noqa: E402
from app.services.auth import AuthService, get_auth_service  # noqa: E402


@pytest_asyncio.fixture
async def admin_app() -> AsyncIterator[tuple[FastAPI, dict[str, str]]]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    auth_service = AuthService(
        settings=Settings(
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
            SECRET_KEY=SecretStr("admin-test-secret-minimum-32-characters"),
            ACCESS_TOKEN_TTL_MINUTES=5,
        )
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        tenant = Tenant(slug="tenant-admin", name="Tenant Admin", status=TenantStatus.ACTIVE)
        role = Role(name=RoleName.ADMIN, description="Admin")
        session.add_all([tenant, role])
        await session.flush()
        user = User(
            tenant_id=tenant.id,
            role_id=role.id,
            email="admin@example.com",
            display_name="Admin",
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
            title="Admin stats session",
            description="",
            created_by_user_id=user.id,
        )
        session.add(goal)
        await session.flush()
        session.add(
            ClientSession(
                tenant_id=tenant.id,
                client_id=client.id,
                goal_id=goal.id,
                status=SessionStatus.ACTIVE,
                created_by_user_id=user.id,
                updated_by_user_id=user.id,
            )
        )
        session.add(
            AuditLog(
                tenant_id=tenant.id,
                actor_user_id=user.id,
                action=AuditAction.ADMIN_CONFIG_CHANGE,
                resource_type="admin_route",
                resource_id="stats",
                reason="admin_route_test",
                metadata_json={"source": "test"},
                correlation_id="admin-route-test",
            )
        )
        await session.commit()
        token = auth_service.issue_access_token(
            user_id=user.id,
            tenant_id=tenant.id,
            role=RoleName.ADMIN,
            email=user.email,
        )
        headers = {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant.id)}

    app = create_app()

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_auth_service] = lambda: auth_service

    try:
        yield app, headers
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_audit_log_returns_list(admin_app: tuple[FastAPI, dict[str, str]]) -> None:
    app, headers = admin_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/audit-log", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert body[0]["action"] == AuditAction.ADMIN_CONFIG_CHANGE.value


@pytest.mark.asyncio
async def test_stats_returns_numbers(admin_app: tuple[FastAPI, dict[str, str]]) -> None:
    app, headers = admin_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/stats", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total_sessions"] == 1
    assert body["total_clients"] == 1
    assert isinstance(body["active_sessions_24h"], int)
