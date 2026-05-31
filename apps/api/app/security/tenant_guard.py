"""Tenant-first FastAPI security guards."""

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status

from app.services.auth import AuthenticatedPrincipal, AuthError, AuthService, get_auth_service


@dataclass(frozen=True)
class TenantContext:
    """Request tenant context after authentication and tenant-boundary validation."""

    tenant_id: UUID
    principal: AuthenticatedPrincipal


async def require_authenticated_principal(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> AuthenticatedPrincipal:
    """Require a valid bearer token and return its principal."""
    try:
        return auth_service.authenticate_bearer(authorization)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


async def require_tenant_context(
    principal: Annotated[AuthenticatedPrincipal, Depends(require_authenticated_principal)],
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
) -> TenantContext:
    """Require an explicit tenant header matching the authenticated tenant claim."""
    if not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context required",
        )

    try:
        tenant_id = UUID(x_tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context denied",
        ) from exc

    if tenant_id != principal.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context denied",
        )

    return TenantContext(tenant_id=tenant_id, principal=principal)
