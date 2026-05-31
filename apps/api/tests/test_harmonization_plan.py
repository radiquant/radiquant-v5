"""Harmonization plan approval gate tests."""

import sys
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

import app.models  # noqa: F401, E402
import app.models.harmonization  # noqa: F401, E402
from app.core.config import Settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db_session, make_async_engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.client import ClientProfile  # noqa: E402
from app.models.harmonization import HarmonizationPlan  # noqa: E402
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus  # noqa: E402
from app.models.session import ClientSession, SessionGoal, SessionStatus  # noqa: E402
from app.services.auth import AuthService, get_auth_service  # noqa: E402


@pytest_asyncio.fixture
async def harmonization_api() -> AsyncIterator[
    tuple[object, async_sessionmaker[AsyncSession], AuthService]
]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    auth_service = AuthService(
        settings=Settings(
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
            SECRET_KEY=SecretStr("harmonization-secret-minimum-32-characters"),
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
    slug: str = "tenant-a",
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


def _headers(auth_service: AuthService, tenant_id: UUID, user_id: UUID) -> dict[str, str]:
    token = auth_service.issue_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        role=RoleName.THERAPIST,
        email="therapist@example.com",
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


async def _create_plan(
    api: object,
    auth_service: AuthService,
    tenant_id: UUID,
    user_id: UUID,
    session_id: UUID,
) -> dict[str, object]:
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as client:
        response = await client.post(
            f"/sessions/{session_id}/harmonization/plans",
            headers=_headers(auth_service, tenant_id, user_id),
            json={
                "session_id": str(session_id),
                "plan_payload_json": {"mode": "balance", "steps": ["review", "approve"]},
            },
        )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_create_plan_creates_draft(
    harmonization_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    api, factory, auth_service = harmonization_api
    tenant_id, user_id, session_id = await _seed_session(factory)

    body = await _create_plan(api, auth_service, tenant_id, user_id, session_id)

    assert body["status"] == "draft"
    assert body["session_id"] == str(session_id)
    assert body["tenant_id"] == str(tenant_id)
    assert body["approved_by_user_id"] is None
    assert body["approved_at"] is None


@pytest.mark.asyncio
async def test_approve_plan_sets_approved_status(
    harmonization_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    api, factory, auth_service = harmonization_api
    tenant_id, user_id, session_id = await _seed_session(factory)
    created = await _create_plan(api, auth_service, tenant_id, user_id, session_id)

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as client:
        response = await client.post(
            f"/sessions/{session_id}/harmonization/plans/{created['id']}/approve",
            headers=_headers(auth_service, tenant_id, user_id),
        )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "approved"
    assert body["approved_by_user_id"] == str(user_id)
    assert body["approved_at"] is not None


@pytest.mark.asyncio
async def test_plan_not_approvable_twice(
    harmonization_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    api, factory, auth_service = harmonization_api
    tenant_id, user_id, session_id = await _seed_session(factory)
    created = await _create_plan(api, auth_service, tenant_id, user_id, session_id)

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as client:
        first = await client.post(
            f"/sessions/{session_id}/harmonization/plans/{created['id']}/approve",
            headers=_headers(auth_service, tenant_id, user_id),
        )
        second = await client.post(
            f"/sessions/{session_id}/harmonization/plans/{created['id']}/approve",
            headers=_headers(auth_service, tenant_id, user_id),
        )

    assert first.status_code == 200
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_list_plans_tenant_scoped(
    harmonization_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    api, factory, auth_service = harmonization_api
    tenant_id, user_id, session_id = await _seed_session(factory, slug="tenant-a")
    other_tenant_id, other_user_id, other_session_id = await _seed_session(
        factory,
        slug="tenant-b",
    )
    await _create_plan(api, auth_service, tenant_id, user_id, session_id)
    await _create_plan(api, auth_service, other_tenant_id, other_user_id, other_session_id)

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as client:
        response = await client.get(
            f"/sessions/{session_id}/harmonization/plans",
            headers=_headers(auth_service, tenant_id, user_id),
        )

    body = response.json()
    assert response.status_code == 200
    assert len(body["items"]) == 1
    assert body["items"][0]["tenant_id"] == str(tenant_id)


@pytest.mark.asyncio
async def test_approve_writes_audit_event(
    harmonization_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    api, factory, auth_service = harmonization_api
    tenant_id, user_id, session_id = await _seed_session(factory)
    created = await _create_plan(api, auth_service, tenant_id, user_id, session_id)

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as client:
        response = await client.post(
            f"/sessions/{session_id}/harmonization/plans/{created['id']}/approve",
            headers=_headers(auth_service, tenant_id, user_id),
        )
    assert response.status_code == 200

    async with factory() as session:
        action = await session.scalar(
            text(
                "select action from audit_logs where resource_id = :resource_id"
            ),
            {"resource_id": str(created["id"])},
        )

    assert action == "harmonization_plan_approved"


@pytest.mark.asyncio
async def test_create_plan_requires_valid_session(
    harmonization_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    api, factory, auth_service = harmonization_api
    tenant_id, user_id, _session_id = await _seed_session(factory)
    missing_session_id = uuid4()

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as client:
        response = await client.post(
            f"/sessions/{missing_session_id}/harmonization/plans",
            headers=_headers(auth_service, tenant_id, user_id),
            json={
                "session_id": str(missing_session_id),
                "plan_payload_json": {"mode": "balance"},
            },
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_created_plan_is_not_auto_approved(
    harmonization_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    api, factory, auth_service = harmonization_api
    tenant_id, user_id, session_id = await _seed_session(factory)
    created = await _create_plan(api, auth_service, tenant_id, user_id, session_id)

    async with factory() as session:
        stored = await session.scalar(
            select(HarmonizationPlan).where(HarmonizationPlan.id == UUID(str(created["id"])))
        )

    assert stored is not None
    assert stored.status == "draft"
    assert stored.approved_by_user_id is None
