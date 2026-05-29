"""ConsentService tests for future processing gates."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.base import Base
from app.db.session import make_async_engine
from app.models.client import ClientConsent, ClientProfile, ConsentPurpose, ConsentStatus
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus
from app.security.passwords import hash_password
from app.services.consent import ConsentRequiredError, ConsentService


@pytest_asyncio.fixture
async def consent_session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    try:
        yield session_factory
    finally:
        await engine.dispose()


async def _seed_client(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    tenant_slug: str = "tenant-a",
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
            email=f"{tenant_slug}@example.com",
            display_name=tenant_slug,
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


async def _record_consent(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    tenant: Tenant,
    user: User,
    client: ClientProfile,
    status: ConsentStatus = ConsentStatus.GRANTED,
    purpose: ConsentPurpose = ConsentPurpose.ANALYSIS,
    expires_at: datetime | None = None,
) -> ClientConsent:
    async with session_factory() as session:
        now = datetime.now(UTC)
        consent = ClientConsent(
            tenant_id=tenant.id,
            client_id=client.id,
            purpose=purpose,
            status=status,
            consent_text_version="v1",
            recorded_by_user_id=user.id,
            granted_at=now,
            revoked_at=now if status == ConsentStatus.REVOKED else None,
            expires_at=expires_at,
        )
        session.add(consent)
        await session.commit()
        return consent


@pytest.mark.asyncio
async def test_assert_active_consent_accepts_granted_non_expired(
    consent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant, user, client = await _seed_client(consent_session_factory)
    consent = await _record_consent(consent_session_factory, tenant=tenant, user=user, client=client)

    async with consent_session_factory() as session:
        result = await ConsentService(session).assert_active_consent(
            tenant_id=tenant.id,
            client_id=client.id,
            purpose=ConsentPurpose.ANALYSIS,
        )

    assert result.consent_id == consent.id
    assert result.tenant_id == tenant.id
    assert result.client_id == client.id
    assert result.purpose == ConsentPurpose.ANALYSIS


@pytest.mark.asyncio
async def test_assert_analysis_allowed_uses_analysis_purpose(
    consent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant, user, client = await _seed_client(consent_session_factory)
    await _record_consent(consent_session_factory, tenant=tenant, user=user, client=client)

    async with consent_session_factory() as session:
        result = await ConsentService(session).assert_analysis_allowed(tenant_id=tenant.id, client_id=client.id)

    assert result.purpose == ConsentPurpose.ANALYSIS


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "expires_delta", "expected_reason"),
    [
        (ConsentStatus.REVOKED, None, "revoked"),
        (ConsentStatus.GRANTED, timedelta(seconds=-1), "expired"),
    ],
)
async def test_assert_active_consent_rejects_revoked_or_expired_with_safe_detail(
    consent_session_factory: async_sessionmaker[AsyncSession],
    status: ConsentStatus,
    expires_delta: timedelta | None,
    expected_reason: str,
) -> None:
    tenant, user, client = await _seed_client(consent_session_factory)
    now = datetime.now(UTC)
    await _record_consent(
        consent_session_factory,
        tenant=tenant,
        user=user,
        client=client,
        status=status,
        expires_at=now + expires_delta if expires_delta is not None else None,
    )

    async with consent_session_factory() as session:
        with pytest.raises(ConsentRequiredError) as exc_info:
            await ConsentService(session).assert_active_consent(
                tenant_id=tenant.id,
                client_id=client.id,
                purpose=ConsentPurpose.ANALYSIS,
                now=now,
            )

    assert str(exc_info.value) == ConsentRequiredError.public_detail
    assert exc_info.value.reason == expected_reason


@pytest.mark.asyncio
async def test_latest_revoked_consent_blocks_older_grant(
    consent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant, user, client = await _seed_client(consent_session_factory)
    await _record_consent(consent_session_factory, tenant=tenant, user=user, client=client, status=ConsentStatus.GRANTED)
    await _record_consent(consent_session_factory, tenant=tenant, user=user, client=client, status=ConsentStatus.REVOKED)

    async with consent_session_factory() as session:
        with pytest.raises(ConsentRequiredError) as exc_info:
            await ConsentService(session).assert_analysis_allowed(tenant_id=tenant.id, client_id=client.id)

    assert str(exc_info.value) == ConsentRequiredError.public_detail
    assert exc_info.value.reason == "revoked"


@pytest.mark.asyncio
async def test_missing_consent_uses_safe_public_detail(
    consent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant, _user, client = await _seed_client(consent_session_factory)

    async with consent_session_factory() as session:
        with pytest.raises(ConsentRequiredError) as exc_info:
            await ConsentService(session).assert_analysis_allowed(tenant_id=tenant.id, client_id=client.id)

    assert str(exc_info.value) == ConsentRequiredError.public_detail
    assert exc_info.value.reason == "missing"


@pytest.mark.asyncio
async def test_wrong_tenant_uses_same_safe_public_detail(
    consent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_a, user_a, client_a = await _seed_client(consent_session_factory, tenant_slug="tenant-a")
    tenant_b, _user_b, _client_b = await _seed_client(consent_session_factory, tenant_slug="tenant-b")
    await _record_consent(consent_session_factory, tenant=tenant_a, user=user_a, client=client_a)

    async with consent_session_factory() as session:
        with pytest.raises(ConsentRequiredError) as exc_info:
            await ConsentService(session).assert_analysis_allowed(tenant_id=tenant_b.id, client_id=client_a.id)

    assert str(exc_info.value) == ConsentRequiredError.public_detail
    assert exc_info.value.reason == "wrong_tenant"
