"""HRV-gated harmonization tests."""

import sys
from collections.abc import AsyncIterator
from datetime import UTC, datetime
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
import app.services.hrv_gate as hrv_gate_module  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db_session, make_async_engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.client import ClientProfile  # noqa: E402
from app.models.event import EventRecord  # noqa: E402
from app.models.harmonization import HarmonizationPlan  # noqa: E402
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus  # noqa: E402
from app.models.session import ClientSession, SessionGoal, SessionStatus  # noqa: E402
from app.schemas.hrv import HRVGateResult, HRVReading  # noqa: E402
from app.services.auth import AuthService, get_auth_service  # noqa: E402
from app.services.hrv_gate import HRVGateService  # noqa: E402


@pytest_asyncio.fixture
async def hrv_api() -> AsyncIterator[tuple[object, async_sessionmaker[AsyncSession], AuthService]]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    auth_service = AuthService(
        settings=Settings(
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
            SECRET_KEY=SecretStr("hrv-secret-minimum-32-characters"),
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


async def _seed_approved_plan(
    factory: async_sessionmaker[AsyncSession],
    *,
    slug: str = "tenant-hrv-a",
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
        await session.flush()
        plan = HarmonizationPlan(
            session_id=client_session.id,
            tenant_id=tenant.id,
            status="approved",
            plan_payload_json={"mode": "balance"},
            created_by_user_id=user.id,
            approved_by_user_id=user.id,
            approved_at=datetime.now(UTC),
        )
        session.add(plan)
        await session.commit()
        return tenant.id, user.id, client_session.id, plan.id


async def _seed_hrv_event(
    factory: async_sessionmaker[AsyncSession],
    *,
    tenant_id: UUID,
    session_id: UUID,
    coherence_score: float,
) -> None:
    async with factory() as session:
        session.add(
            EventRecord(
                tenant_id=tenant_id,
                event_id=uuid4(),
                event_type="hrv.reading",
                correlation_id=str(uuid4()),
                session_id=session_id,
                resource_type="session",
                resource_id=str(session_id),
                payload_json={
                    "heart_rate_bpm": 72.0,
                    "coherence_score": coherence_score,
                    "measured_at": datetime.now(UTC).isoformat(),
                    "source": "simulated",
                },
            )
        )
        await session.commit()


def _headers(auth_service: AuthService, tenant_id: UUID, user_id: UUID) -> dict[str, str]:
    token = auth_service.issue_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        role=RoleName.THERAPIST,
        email="therapist@example.com",
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


@pytest.mark.asyncio
async def test_hrv_gate_disabled_by_default_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(hrv_gate_module, "FEATURE_HRV_ENABLED", False)

    result = await HRVGateService().evaluate(session_id=uuid4(), tenant_id=uuid4())

    assert result.passed is True
    assert result.threshold == hrv_gate_module.HRV_COHERENCE_THRESHOLD


@pytest.mark.asyncio
async def test_hrv_gate_passes_above_threshold(
    hrv_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(hrv_gate_module, "FEATURE_HRV_ENABLED", True)
    _api, factory, _auth_service = hrv_api
    tenant_id, _user_id, session_id, _plan_id = await _seed_approved_plan(factory)
    await _seed_hrv_event(
        factory,
        tenant_id=tenant_id,
        session_id=session_id,
        coherence_score=0.8,
    )

    async with factory() as session:
        result = await HRVGateService().evaluate(session_id, tenant_id, db=session)

    assert result.passed is True
    assert result.coherence_score == 0.8


@pytest.mark.asyncio
async def test_hrv_gate_blocks_below_threshold(
    hrv_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(hrv_gate_module, "FEATURE_HRV_ENABLED", True)
    api, factory, auth_service = hrv_api
    tenant_id, user_id, session_id, plan_id = await _seed_approved_plan(factory)
    await _seed_hrv_event(
        factory,
        tenant_id=tenant_id,
        session_id=session_id,
        coherence_score=0.1,
    )

    async with AsyncClient(
        transport=ASGITransport(app=api),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/sessions/harmonization/jobs?plan_id={plan_id}",
            headers=_headers(auth_service, tenant_id, user_id),
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "HRV coherence below threshold"


@pytest.mark.asyncio
async def test_hrv_gate_therapist_override_bypasses(
    hrv_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(hrv_gate_module, "FEATURE_HRV_ENABLED", True)
    _api, factory, _auth_service = hrv_api
    tenant_id, _user_id, session_id, _plan_id = await _seed_approved_plan(factory)
    await _seed_hrv_event(
        factory,
        tenant_id=tenant_id,
        session_id=session_id,
        coherence_score=0.1,
    )

    async with factory() as session:
        result = await HRVGateService().evaluate(
            session_id,
            tenant_id,
            therapist_override=True,
            db=session,
        )

    assert result.passed is True
    assert result.override_by_therapist is True


@pytest.mark.asyncio
async def test_hrv_gate_writes_audit_event(
    hrv_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(hrv_gate_module, "FEATURE_HRV_ENABLED", True)
    _api, factory, _auth_service = hrv_api
    tenant_id, _user_id, session_id, _plan_id = await _seed_approved_plan(factory)
    await _seed_hrv_event(
        factory,
        tenant_id=tenant_id,
        session_id=session_id,
        coherence_score=0.7,
    )

    async with factory() as session:
        await HRVGateService().evaluate(session_id, tenant_id, db=session)

    async with factory() as session:
        action = await session.scalar(
            text("select action from audit_logs where resource_id = :resource_id"),
            {"resource_id": str(session_id)},
        )

    assert action == "hrv_gate_evaluated"


def test_hrv_gate_result_schema_valid() -> None:
    reading = HRVReading(
        heart_rate_bpm=70.0,
        coherence_score=0.5,
        measured_at=datetime.now(UTC),
        source="manual",
    )
    result = HRVGateResult(
        passed=True,
        coherence_score=reading.coherence_score,
        threshold=0.35,
        override_by_therapist=False,
    )

    assert result.passed is True
    assert result.coherence_score == 0.5
