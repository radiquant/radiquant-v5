"""Therapist LLM copilot routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.identity import RoleName
from app.schemas.llm_copilot import CopilotRequest, CopilotResponse
from app.security.tenant_guard import TenantContext, require_tenant_context
from app.services.llm_copilot import LLMCopilotService

llm_copilot_router = APIRouter(prefix="/copilot", tags=["llm_copilot"])


@llm_copilot_router.post(
    "/query",
    operation_id="queryLlmCopilot",
    response_model=CopilotResponse,
)
async def query_llm_copilot(
    payload: CopilotRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> CopilotResponse:
    if context.principal.role != RoleName.THERAPIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Therapist role required",
        )
    return await LLMCopilotService().generate(payload, context.tenant_id, session)
