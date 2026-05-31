"""Tenant-scoped report routes."""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.report import ClientReport, TherapistAppendix
from app.security.tenant_guard import TenantContext, require_tenant_context
from app.services.claim_linter import ClaimViolationError
from app.services.report_service import ReportService

reports_router = APIRouter(prefix="/sessions", tags=["reports"])


@reports_router.get(
    "/{session_id}/report",
    operation_id="getSessionReport",
    response_model=ClientReport | TherapistAppendix,
)
async def get_session_report(
    session_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    role: Annotated[Literal["client", "therapist"], Query()] = "client",
) -> ClientReport | TherapistAppendix:
    try:
        if role == "client":
            return await ReportService().build_client_report(
                session_id=session_id,
                tenant_id=context.tenant_id,
                db=session,
            )
        return await ReportService().build_therapist_appendix(
            session_id=session_id,
            tenant_id=context.tenant_id,
            db=session,
        )
    except ClaimViolationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"claim_violations": exc.violations},
        ) from exc
