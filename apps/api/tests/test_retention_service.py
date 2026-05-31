"""Retention policy cleanup tests."""

import sys
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

import app.models  # noqa: F401, E402
import app.models.retention  # noqa: F401, E402
from app.db.base import Base  # noqa: E402
from app.db.session import make_async_engine  # noqa: E402
from app.models.client import (  # noqa: E402
    ClientConsent,
    ClientProfile,
    ConsentPurpose,
    ConsentStatus,
)
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus  # noqa: E402
from app.models.retention import RetentionPolicy  # noqa: E402
from app.models.session import ClientSession, SessionGoal, SessionStatus  # noqa: E402
from app.services.retention_service import RetentionService  # noqa: E402


@pytest_asyncio.fixture
async def retention_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    try:
        yield factory
    finally:
        await engine.dispose()


async def _seed_client_session(
    factory: async_sessionmaker[AsyncSession],
    *,
    slug: str = "tenant-retention-a",
    created_at: datetime | None = None,
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
            created_at=created_at or datetime.now(UTC),
        )
        session.add(client_session)
        await session.commit()
        return tenant.id, client.id, client_session.id


async def _create_policy(
    factory: async_sessionmaker[AsyncSession],
    *,
    tenant_id: UUID,
    data_type: str = "sessions",
    retention_days: int | None = None,
    enabled: bool = True,
) -> RetentionPolicy:
    async with factory() as session:
        kwargs: dict[str, object] = {
            "tenant_id": tenant_id,
            "data_type": data_type,
            "enabled": enabled,
        }
        if retention_days is not None:
            kwargs["retention_days"] = retention_days
        policy = RetentionPolicy(**kwargs)
        session.add(policy)
        await session.commit()
        return policy


@pytest.mark.asyncio
async def test_retention_policy_created_with_defaults(
    retention_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id, _client_id, _session_id = await _seed_client_session(retention_factory)
    policy = await _create_policy(retention_factory, tenant_id=tenant_id)

    assert policy.data_type == "sessions"
    assert policy.retention_days == 365
    assert policy.enabled is True
    assert policy.created_at is not None


@pytest.mark.asyncio
async def test_cleanup_anonymizes_expired_records(
    retention_factory: async_sessionmaker[AsyncSession],
) -> None:
    old_date = datetime.now(UTC) - timedelta(days=400)
    tenant_id, client_id, _session_id = await _seed_client_session(
        retention_factory,
        created_at=old_date,
    )
    await _create_policy(retention_factory, tenant_id=tenant_id, retention_days=30)

    async with retention_factory() as session:
        report = await RetentionService().run_cleanup(tenant_id, session)

    async with retention_factory() as session:
        client = await session.scalar(select(ClientProfile).where(ClientProfile.id == client_id))
        session_status = await session.scalar(text("select status from sessions"))

    assert report.data_type == "sessions"
    assert report.records_processed == 1
    assert report.records_anonymized == 1
    assert client is not None
    assert client.display_name.startswith("ANONYMIZED-")
    assert session_status == "anonymized"


@pytest.mark.asyncio
async def test_cleanup_skips_non_expired_records(
    retention_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id, client_id, _session_id = await _seed_client_session(retention_factory)
    await _create_policy(retention_factory, tenant_id=tenant_id, retention_days=365)

    async with retention_factory() as session:
        report = await RetentionService().run_cleanup(tenant_id, session)

    async with retention_factory() as session:
        client = await session.scalar(select(ClientProfile).where(ClientProfile.id == client_id))

    assert report.records_processed == 0
    assert report.records_anonymized == 0
    assert client is not None
    assert client.display_name == "Client tenant-retention-a"


@pytest.mark.asyncio
async def test_cleanup_tenant_scoped(
    retention_factory: async_sessionmaker[AsyncSession],
) -> None:
    old_date = datetime.now(UTC) - timedelta(days=400)
    tenant_id, client_id, _session_id = await _seed_client_session(
        retention_factory,
        slug="tenant-retention-a",
        created_at=old_date,
    )
    other_tenant_id, other_client_id, _other_session_id = await _seed_client_session(
        retention_factory,
        slug="tenant-retention-b",
        created_at=old_date,
    )
    await _create_policy(retention_factory, tenant_id=tenant_id, retention_days=30)
    await _create_policy(retention_factory, tenant_id=other_tenant_id, retention_days=30)

    async with retention_factory() as session:
        report = await RetentionService().run_cleanup(tenant_id, session)

    async with retention_factory() as session:
        client = await session.scalar(select(ClientProfile).where(ClientProfile.id == client_id))
        other_client = await session.scalar(
            select(ClientProfile).where(ClientProfile.id == other_client_id)
        )

    assert report.tenant_id == tenant_id
    assert report.records_anonymized == 1
    assert client is not None
    assert client.display_name.startswith("ANONYMIZED-")
    assert other_client is not None
    assert other_client.display_name == "Client tenant-retention-b"


@pytest.mark.asyncio
async def test_cleanup_writes_audit_event(
    retention_factory: async_sessionmaker[AsyncSession],
) -> None:
    old_date = datetime.now(UTC) - timedelta(days=400)
    tenant_id, _client_id, _session_id = await _seed_client_session(
        retention_factory,
        created_at=old_date,
    )
    await _create_policy(retention_factory, tenant_id=tenant_id, retention_days=30)

    async with retention_factory() as session:
        report = await RetentionService().run_cleanup(tenant_id, session)

    async with retention_factory() as session:
        actions = list(
            (
                await session.execute(
                    text("select action from audit_logs where resource_id = :resource_id"),
                    {"resource_id": str(tenant_id)},
                )
            )
            .scalars()
            .all()
        )

    assert report.records_processed == 1
    assert "retention_cleanup" in actions
