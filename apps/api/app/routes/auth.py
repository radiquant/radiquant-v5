"""Identity routes for the security core.

Only login/logout are exposed here. Client/session/workflow/engine feature routes
remain blocked until their contracts and tenant/consent gates are implemented.
"""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.audit import AuditAction
from app.models.identity import Role, Tenant, TenantStatus, User, UserStatus
from app.schemas.auth import LoginRequest, LogoutResponse, TokenResponse
from app.security.passwords import PasswordHashError, verify_password
from app.security.tenant_guard import require_authenticated_principal
from app.services.audit import AuditService
from app.services.auth import AuthService, AuthenticatedPrincipal, get_auth_service

router = APIRouter(prefix="/auth", tags=["identity"])


def _correlation_id(request: Request) -> str:
    header_value = request.headers.get("X-Correlation-ID")
    return header_value if header_value else str(uuid4())


@router.post("/login", operation_id="login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Authenticate a tenant-scoped user and issue a bearer token."""
    tenant = await session.scalar(select(Tenant).where(Tenant.slug == payload.tenant_slug))
    if tenant is None or tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    row = await session.execute(
        select(User, Role)
        .join(Role, User.role_id == Role.id)
        .where(User.tenant_id == tenant.id, User.email == str(payload.email))
    )
    result = row.one_or_none()
    user: User | None = None
    role: Role | None = None
    if result is not None:
        user, role = result

    password_matches = False
    if user is not None and user.status == UserStatus.ACTIVE:
        try:
            password_matches = verify_password(payload.password, user.password_hash)
        except PasswordHashError:
            password_matches = False

    audit = AuditService(session)
    correlation_id = _correlation_id(request)
    if user is None or role is None or not password_matches:
        await audit.append(
            tenant_id=tenant.id,
            action=AuditAction.LOGIN_SECURITY_EVENT,
            resource_type="identity.login",
            correlation_id=correlation_id,
            actor_user_id=user.id if user is not None else None,
            reason="login_failed",
            metadata_json={"outcome": "denied"},
        )
        await session.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    await audit.append(
        tenant_id=tenant.id,
        action=AuditAction.LOGIN_SECURITY_EVENT,
        resource_type="identity.login",
        correlation_id=correlation_id,
        actor_user_id=user.id,
        reason="login_success",
        metadata_json={"outcome": "allowed"},
    )
    await session.commit()

    access_token = auth_service.issue_access_token(
        user_id=user.id,
        tenant_id=tenant.id,
        role=role.name,
        email=user.email,
    )
    return TokenResponse(
        access_token=access_token,
        tenant_id=tenant.id,
        user_id=user.id,
        role=role.name,
    )


@router.post("/logout", operation_id="logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[AuthenticatedPrincipal, Depends(require_authenticated_principal)],
) -> LogoutResponse:
    """Record a logout security event for the authenticated principal."""
    audit = AuditService(session)
    await audit.append(
        tenant_id=principal.tenant_id,
        action=AuditAction.LOGIN_SECURITY_EVENT,
        resource_type="identity.logout",
        correlation_id=_correlation_id(request),
        actor_user_id=principal.user_id,
        reason="logout",
        metadata_json={"outcome": "acknowledged"},
    )
    await session.commit()
    return LogoutResponse()
