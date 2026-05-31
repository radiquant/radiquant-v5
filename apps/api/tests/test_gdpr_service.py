"""GDPR export, anonymization, and retention tests."""

import sys
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

import app.models  # noqa: F401, E402
from app.core.config import Settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db_session, make_async_engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.client import (  # noqa: E402
    ClientConsent,
    ClientProfile,
    ConsentPurpose,
    ConsentStatus,
)
from app.models.event import EventRecord  # noqa: E402
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus  # noqa: E402
from app.models.session import ClientSession, SessionGoal, SessionStatus  # noqa: E402
from app.services.auth import AuthService, get_auth_service  # noqa: E402
from app.services.gdpr_service import GdprService  # noqa: E402


@pytest_asyncio.fixture
async def gdpr_api() -> AsyncIterator[tuple[object, async_sessionmaker[AsyncSession], AuthService]]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    auth_service = AuthService(
        settings=Settings(
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
            SECRET_KEY=SecretStr("gdpr-secret-minimum-32-characters"),
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


async def _seed_client_bundle(
    factory: async_sessionmaker[AsyncSession],
    *,
    slug: str = "tenant-gdpr-a",
) -> tuple[UUID, UUID, UUID, UUID]:
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
            display_name="Client GDPR",
            client_code=f"{slug}-client",
            created_by_user_id=user.id,
            updated_by_user_id=user.id,
        )
        session.add(client)
        await session.flush()
        consent = ClientConsent(
            tenant_id=tenant.id,
            client_id=client.id,
            purpose=ConsentPurpose.ANALYSIS,
            status=ConsentStatus.GRANTED,
            consent_text_version="v1",
            recorded_by_user_id=user.id,
            granted_at=datetime.now(UTC),
        )
        session.add(consent)
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
        event = EventRecord(
            tenant_id=tenant.id,
            event_id=uuid4(),
            event_type="client.profile.exportable",
            correlation_id=str(uuid4()),
            session_id=client_session.id,
            resource_type="client_profile",
            resource_id=str(client.id),
            payload_json={
                "summary": "safe event",
                "result_payload_json": {"raw": "secret-result"},
                "nested": {"raw_debug": "secret-debug", "visible": "kept"},
            },
        )
        session.add(event)
        await session.commit()
        return tenant.id, user.id, client.id, client_session.id


def _headers(auth_service: AuthService, tenant_id: UUID, user_id: UUID) -> dict[str, str]:
    token = auth_service.issue_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        role=RoleName.THERAPIST,
        email="therapist@example.com",
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


@pytest.mark.asyncio
async def test_export_includes_all_data_types(
    gdpr_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    _api, factory, _auth_service = gdpr_api
    tenant_id, _user_id, client_id, _session_id = await _seed_client_bundle(factory)

    async with factory() as session:
        export = await GdprService().export(client_id, tenant_id, session)

    assert export.client_id == client_id
    assert export.tenant_id == tenant_id
    assert export.profile["display_name"] == "Client GDPR"
    assert len(export.profile["consents"]) == 1
    assert len(export.sessions) == 1
    assert len(export.events) == 1


@pytest.mark.asyncio
async def test_export_excludes_raw_payload(
    gdpr_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    _api, factory, _auth_service = gdpr_api
    tenant_id, _user_id, client_id, _session_id = await _seed_client_bundle(factory)

    async with factory() as session:
        export = await GdprService().export(client_id, tenant_id, session)

    event_payload = export.events[0]["payload_json"]
    assert "result_payload_json" not in event_payload
    assert "raw_debug" not in event_payload["nested"]
    assert "secret-result" not in str(export.model_dump(mode="json"))
    assert "secret-debug" not in str(export.model_dump(mode="json"))


@pytest.mark.asyncio
async def test_export_tenant_scoped(
    gdpr_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    _api, factory, _auth_service = gdpr_api
    _tenant_id, _user_id, client_id, _session_id = await _seed_client_bundle(
        factory,
        slug="tenant-gdpr-a",
    )
    other_tenant_id, _other_user_id, _other_client_id, _other_session_id = (
        await _seed_client_bundle(factory, slug="tenant-gdpr-b")
    )

    async with factory() as session:
        with pytest.raises(HTTPException) as exc_info:
            await GdprService().export(client_id, other_tenant_id, session)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_anonymize_replaces_pii(
    gdpr_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    _api, factory, _auth_service = gdpr_api
    tenant_id, _user_id, client_id, _session_id = await _seed_client_bundle(factory)

    async with factory() as session:
        response = await GdprService().anonymize(client_id, tenant_id, session)

    async with factory() as session:
        client = await session.scalar(select(ClientProfile).where(ClientProfile.id == client_id))

    assert response.client_id == client_id
    assert client is not None
    assert client.display_name.startswith("ANONYMIZED-")
    assert client.client_code is None
    assert "display_name" in response.fields_anonymized


@pytest.mark.asyncio
async def test_anonymize_revokes_consents(
    gdpr_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    _api, factory, _auth_service = gdpr_api
    tenant_id, _user_id, client_id, _session_id = await _seed_client_bundle(factory)

    async with factory() as session:
        await GdprService().anonymize(client_id, tenant_id, session)

    async with factory() as session:
        consent = await session.scalar(
            select(ClientConsent).where(ClientConsent.client_id == client_id)
        )

    assert consent is not None
    assert consent.status == ConsentStatus.REVOKED
    assert consent.revoked_at is not None


@pytest.mark.asyncio
async def test_anonymize_does_not_hard_delete(
    gdpr_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    _api, factory, _auth_service = gdpr_api
    tenant_id, _user_id, client_id, _session_id = await _seed_client_bundle(factory)

    async with factory() as session:
        await GdprService().anonymize(client_id, tenant_id, session)

    async with factory() as session:
        client_count = await session.scalar(
            select(func.count()).select_from(ClientProfile).where(ClientProfile.id == client_id)
        )
        session_statuses = list(
            (
                await session.execute(text("select status from sessions"))
            )
            .scalars()
            .all()
        )

    assert client_count == 1
    assert "anonymized" in session_statuses


@pytest.mark.asyncio
async def test_retain_extends_retention(
    gdpr_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    _api, factory, _auth_service = gdpr_api
    tenant_id, _user_id, client_id, _session_id = await _seed_client_bundle(factory)
    before = datetime.now(UTC)

    async with factory() as session:
        response = await GdprService().retain(client_id, tenant_id, "legal_hold", session)

    assert response.client_id == client_id
    assert response.reason == "legal_hold"
    assert (response.retained_until - before).days >= 364


@pytest.mark.asyncio
async def test_gdpr_audit_events_written(
    gdpr_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
) -> None:
    api, factory, auth_service = gdpr_api
    tenant_id, user_id, client_id, _session_id = await _seed_client_bundle(factory)

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as client:
        export_response = await client.get(
            f"/clients/{client_id}/export",
            headers=_headers(auth_service, tenant_id, user_id),
        )
        retain_response = await client.post(
            f"/clients/{client_id}/retain?reason=legal_hold",
            headers=_headers(auth_service, tenant_id, user_id),
        )
        delete_response = await client.delete(
            f"/clients/{client_id}",
            headers=_headers(auth_service, tenant_id, user_id),
        )

    assert export_response.status_code == 200
    assert retain_response.status_code == 200
    assert delete_response.status_code == 200

    async with factory() as session:
        actions = list(
            (
                await session.execute(
                    text("select action from audit_logs where resource_id = :resource_id"),
                    {"resource_id": str(client_id)},
                )
            )
            .scalars()
            .all()
        )

    assert "gdpr_export" in actions
    assert "gdpr_retain" in actions
    assert "gdpr_anonymize" in actions
