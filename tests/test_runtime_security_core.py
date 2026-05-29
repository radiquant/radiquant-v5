"""Runtime DB, auth service, and tenant guard negative tests."""

from datetime import timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.config import Settings
from app.db.session import make_async_engine, make_async_sessionmaker
from app.models.identity import RoleName
from app.security.tenant_guard import TenantContext, require_tenant_context
from app.services.auth import AuthService, get_auth_service


@pytest.fixture
def auth_service() -> AuthService:
    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SECRET_KEY="test-secret-key-minimum-32-characters",
        ACCESS_TOKEN_TTL_MINUTES=5,
    )
    return AuthService(settings=settings)


@pytest.fixture
def protected_app(auth_service: AuthService) -> FastAPI:
    app = FastAPI()
    app.dependency_overrides[get_auth_service] = lambda: auth_service

    @app.get("/_test/tenant-protected")
    async def tenant_protected(context: TenantContext = Depends(require_tenant_context)) -> dict[str, str]:
        return {
            "tenant_id": str(context.tenant_id),
            "user_id": str(context.principal.user_id),
            "role": context.principal.role.value,
        }

    return app


@pytest.mark.asyncio
async def test_async_db_session_factory_executes_query() -> None:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = make_async_sessionmaker(engine)

    try:
        async with session_factory() as session:
            result = await session.execute(text("select 1"))
            assert result.scalar_one() == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_tenant_guard_accepts_matching_authenticated_tenant(
    protected_app: FastAPI,
    auth_service: AuthService,
) -> None:
    user_id = uuid4()
    tenant_id = uuid4()
    token = auth_service.issue_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        role=RoleName.THERAPIST,
        email="therapist@example.test",
    )

    async with AsyncClient(transport=ASGITransport(app=protected_app), base_url="http://test") as client:
        response = await client.get(
            "/_test/tenant-protected",
            headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)},
        )

    assert response.status_code == 200
    assert response.json() == {
        "tenant_id": str(tenant_id),
        "user_id": str(user_id),
        "role": RoleName.THERAPIST.value,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("headers", "expected_status"),
    [
        ({}, 401),
        ({"Authorization": "not-bearer abc"}, 401),
        ({"Authorization": "Bearer definitely.invalid.token"}, 401),
    ],
)
async def test_auth_negative_cases_are_rejected(
    protected_app: FastAPI,
    headers: dict[str, str],
    expected_status: int,
) -> None:
    async with AsyncClient(transport=ASGITransport(app=protected_app), base_url="http://test") as client:
        response = await client.get("/_test/tenant-protected", headers=headers)

    assert response.status_code == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize("tenant_header", [None, "not-a-uuid"])
async def test_tenant_guard_rejects_missing_or_malformed_tenant_header(
    protected_app: FastAPI,
    auth_service: AuthService,
    tenant_header: str | None,
) -> None:
    tenant_id = uuid4()
    token = auth_service.issue_access_token(user_id=uuid4(), tenant_id=tenant_id, role=RoleName.ADMIN)
    headers = {"Authorization": f"Bearer {token}"}
    if tenant_header is not None:
        headers["X-Tenant-ID"] = tenant_header

    async with AsyncClient(transport=ASGITransport(app=protected_app), base_url="http://test") as client:
        response = await client.get("/_test/tenant-protected", headers=headers)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_tenant_guard_rejects_cross_tenant_request(
    protected_app: FastAPI,
    auth_service: AuthService,
) -> None:
    token = auth_service.issue_access_token(user_id=uuid4(), tenant_id=uuid4(), role=RoleName.ADMIN)

    async with AsyncClient(transport=ASGITransport(app=protected_app), base_url="http://test") as client:
        response = await client.get(
            "/_test/tenant-protected",
            headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": str(uuid4())},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Tenant context denied"


@pytest.mark.asyncio
async def test_auth_service_rejects_token_without_required_tenant_claim(
    protected_app: FastAPI,
    auth_service: AuthService,
) -> None:
    token = jwt.encode(
        {"sub": str(uuid4()), "role": RoleName.ADMIN.value},
        auth_service.settings.secret_key.get_secret_value(),
        algorithm="HS256",
    )

    async with AsyncClient(transport=ASGITransport(app=protected_app), base_url="http://test") as client:
        response = await client.get(
            "/_test/tenant-protected",
            headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": str(uuid4())},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_service_rejects_expired_token(
    protected_app: FastAPI,
    auth_service: AuthService,
) -> None:
    token = auth_service.issue_access_token(
        user_id=uuid4(),
        tenant_id=uuid4(),
        role=RoleName.ADMIN,
        expires_delta=timedelta(seconds=-1),
    )

    async with AsyncClient(transport=ASGITransport(app=protected_app), base_url="http://test") as client:
        response = await client.get(
            "/_test/tenant-protected",
            headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": str(uuid4())},
        )

    assert response.status_code == 401
