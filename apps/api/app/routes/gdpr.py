"""Tenant-scoped GDPR routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.gdpr import GdprDeleteResponse, GdprExportResponse, GdprRetainResponse
from app.security.tenant_guard import TenantContext, require_tenant_context
from app.services.gdpr_service import GdprService

gdpr_router = APIRouter(prefix="/clients", tags=["gdpr"])


@gdpr_router.get(
    "/{client_id}/export",
    operation_id="exportClientGdprData",
    response_model=GdprExportResponse,
)
async def export_client_gdpr_data(
    client_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> GdprExportResponse:
    return await GdprService().export(client_id, context.tenant_id, session)


@gdpr_router.delete(
    "/{client_id}",
    operation_id="anonymizeClientGdprData",
    response_model=GdprDeleteResponse,
)
async def anonymize_client_gdpr_data(
    client_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> GdprDeleteResponse:
    return await GdprService().anonymize(client_id, context.tenant_id, session)


@gdpr_router.post(
    "/{client_id}/retain",
    operation_id="retainClientGdprData",
    response_model=GdprRetainResponse,
)
async def retain_client_gdpr_data(
    client_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    reason: Annotated[str, Query(min_length=1)],
) -> GdprRetainResponse:
    return await GdprService().retain(client_id, context.tenant_id, reason, session)
