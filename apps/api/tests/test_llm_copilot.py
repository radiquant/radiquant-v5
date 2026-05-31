"""LLM therapist copilot tests."""

import json
import sys
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

import app.models  # noqa: F401, E402
import app.services.llm_copilot as llm_copilot_module  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db_session, make_async_engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.client import ClientProfile  # noqa: E402
from app.models.identity import Role, RoleName, Tenant, TenantStatus, User, UserStatus  # noqa: E402
from app.models.session import ClientSession, SessionGoal, SessionStatus  # noqa: E402
from app.schemas.llm_copilot import CopilotRequest, CopilotResponse  # noqa: E402
from app.services.auth import AuthService, get_auth_service  # noqa: E402
from app.services.claim_linter import ClaimLinterService, ClaimViolationError  # noqa: E402
from app.services.llm_copilot import LLMCopilotService  # noqa: E402


@pytest_asyncio.fixture
async def copilot_api() -> AsyncIterator[
    tuple[object, async_sessionmaker[AsyncSession], AuthService]
]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    auth_service = AuthService(
        settings=Settings(
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
            SECRET_KEY=SecretStr("llm-copilot-secret-minimum-32-chars"),
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
    slug: str = "tenant-copilot-a",
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


@pytest.mark.asyncio
async def test_copilot_disabled_by_default_returns_503(
    copilot_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(llm_copilot_module, "FEATURE_LLM_COPILOT", False)
    api, factory, auth_service = copilot_api
    tenant_id, user_id, session_id = await _seed_session(factory)

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as client:
        response = await client.post(
            "/copilot/query",
            headers=_headers(auth_service, tenant_id, user_id),
            json={
                "session_id": str(session_id),
                "question": "Bitte zusammenfassen",
                "role": "therapist",
            },
        )

    assert response.status_code == 503
    assert response.json()["detail"] == "LLM Copilot feature not enabled"


@pytest.mark.asyncio
async def test_copilot_redacts_pii_in_question(
    copilot_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(llm_copilot_module, "FEATURE_LLM_COPILOT", True)
    _api, factory, _auth_service = copilot_api
    tenant_id, _user_id, session_id = await _seed_session(factory)
    request = CopilotRequest(
        session_id=session_id,
        question="name Max email max@example.com phone +49 123456789",
        role="therapist",
    )

    async with factory() as session:
        response = await LLMCopilotService().generate(request, tenant_id, session)

    assert response.pii_redacted is True
    assert "max@example.com" not in response.answer
    assert "+49 123456789" not in response.answer
    assert "[REDACTED]" in response.answer


@pytest.mark.asyncio
async def test_copilot_claim_linter_runs_on_answer(
    copilot_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(llm_copilot_module, "FEATURE_LLM_COPILOT", True)
    _api, factory, _auth_service = copilot_api
    tenant_id, _user_id, session_id = await _seed_session(factory)

    def reject_answer(self: ClaimLinterService, text: str) -> None:
        raise ClaimViolationError(["medizinisch"])

    monkeypatch.setattr(ClaimLinterService, "lint", reject_answer)
    request = CopilotRequest(session_id=session_id, question="Was bedeutet das?", role="therapist")

    async with factory() as session:
        response = await LLMCopilotService().generate(request, tenant_id, session)

    assert response.claim_violations == ["medizinisch"]


@pytest.mark.asyncio
async def test_copilot_audit_event_written(
    copilot_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(llm_copilot_module, "FEATURE_LLM_COPILOT", True)
    _api, factory, _auth_service = copilot_api
    tenant_id, _user_id, session_id = await _seed_session(factory)
    request = CopilotRequest(
        session_id=session_id,
        question="email max@example.com",
        role="therapist",
    )

    async with factory() as session:
        await LLMCopilotService().generate(request, tenant_id, session)

    async with factory() as session:
        row = (
            await session.execute(
                text(
                    "select action, metadata_json from audit_logs "
                    "where resource_id = :resource_id"
                ),
                {"resource_id": str(session_id)},
            )
        ).first()

    assert row is not None
    metadata_json = json.loads(row[1]) if isinstance(row[1], str) else row[1]
    assert row[0] == "llm_copilot_query"
    assert metadata_json["details"]["pii_redacted"] is True


def test_copilot_response_schema_valid() -> None:
    response = CopilotResponse(
        answer="[Copilot-Simulation] ok",
        pii_redacted=False,
        claim_violations=[],
        model_used="copilot-simulation",
        generated_at=datetime.now(UTC),
    )

    assert response.model_used == "copilot-simulation"
    assert response.claim_violations == []


@pytest.mark.asyncio
async def test_copilot_tenant_scoped(
    copilot_api: tuple[object, async_sessionmaker[AsyncSession], AuthService],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(llm_copilot_module, "FEATURE_LLM_COPILOT", True)
    _api, factory, _auth_service = copilot_api
    tenant_id, _user_id, session_id = await _seed_session(factory, slug="tenant-copilot-a")
    other_tenant_id, _other_user_id, _other_session_id = await _seed_session(
        factory,
        slug="tenant-copilot-b",
    )
    request = CopilotRequest(
        session_id=session_id,
        question="Bitte zusammenfassen",
        role="therapist",
    )

    async with factory() as session:
        with pytest.raises(HTTPException) as exc_info:
            await LLMCopilotService().generate(request, other_tenant_id, session)

    assert exc_info.value.status_code == 404
    assert tenant_id != other_tenant_id
