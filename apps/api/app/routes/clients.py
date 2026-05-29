"""Tenant-guarded client profile and consent routes."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.audit import AuditAction
from app.models.client import ClientConsent, ClientProfile, ClientStatus, ConsentStatus
from app.schemas.client import (
    ClientConsentCreate,
    ClientConsentListResponse,
    ClientConsentResponse,
    ClientProfileCreate,
    ClientProfileListResponse,
    ClientProfileResponse,
    ClientProfileUpdate,
)
from app.security.tenant_guard import TenantContext, require_tenant_context
from app.services.audit import AuditService

router = APIRouter(prefix="/clients", tags=["clients"])


def _correlation_id(request: Request) -> str:
    header_value = request.headers.get("X-Correlation-ID")
    return header_value if header_value else str(uuid4())


async def _get_client_or_404(session: AsyncSession, tenant_id: UUID, client_id: UUID) -> ClientProfile:
    client = await session.scalar(
        select(ClientProfile).where(ClientProfile.id == client_id, ClientProfile.tenant_id == tenant_id)
    )
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@router.post("", operation_id="createClientProfile", response_model=ClientProfileResponse, status_code=201)
async def create_client_profile(
    payload: ClientProfileCreate,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> ClientProfile:
    """Create a tenant-scoped human client profile."""
    client = ClientProfile(
        tenant_id=context.tenant_id,
        display_name=payload.display_name,
        client_code=payload.client_code,
        created_by_user_id=context.principal.user_id,
        updated_by_user_id=context.principal.user_id,
    )
    session.add(client)
    await session.flush()

    await AuditService(session).append(
        tenant_id=context.tenant_id,
        actor_user_id=context.principal.user_id,
        action=AuditAction.CLIENT_CREATE_UPDATE_DELETE,
        resource_type="client_profile",
        resource_id=str(client.id),
        reason="client_created",
        correlation_id=_correlation_id(request),
        metadata_json={"outcome": "created"},
    )
    await session.commit()
    await session.refresh(client)
    return client


@router.get("", operation_id="listClientProfiles", response_model=ClientProfileListResponse)
async def list_client_profiles(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    status_filter: Annotated[ClientStatus | None, Query(alias="status")] = None,
) -> ClientProfileListResponse:
    """List client profiles for the authenticated tenant only."""
    statement = select(ClientProfile).where(ClientProfile.tenant_id == context.tenant_id)
    if status_filter is not None:
        statement = statement.where(ClientProfile.status == status_filter)
    statement = statement.order_by(ClientProfile.created_at, ClientProfile.id).limit(limit).offset(offset)
    clients = list((await session.execute(statement)).scalars().all())
    return ClientProfileListResponse(
        items=[ClientProfileResponse.model_validate(client) for client in clients], limit=limit, offset=offset
    )


@router.get("/{client_id}", operation_id="getClientProfile", response_model=ClientProfileResponse)
async def get_client_profile(
    client_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> ClientProfile:
    """Return a single client profile if it belongs to the authenticated tenant."""
    return await _get_client_or_404(session, context.tenant_id, client_id)


@router.patch("/{client_id}", operation_id="updateClientProfile", response_model=ClientProfileResponse)
async def update_client_profile(
    client_id: UUID,
    payload: ClientProfileUpdate,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> ClientProfile:
    """Update safe profile fields for a tenant-owned client."""
    client = await _get_client_or_404(session, context.tenant_id, client_id)
    if payload.display_name is not None:
        client.display_name = payload.display_name
    if payload.client_code is not None:
        client.client_code = payload.client_code
    if payload.status is not None:
        client.status = payload.status
    client.updated_by_user_id = context.principal.user_id

    await session.flush()
    await AuditService(session).append(
        tenant_id=context.tenant_id,
        actor_user_id=context.principal.user_id,
        action=AuditAction.CLIENT_CREATE_UPDATE_DELETE,
        resource_type="client_profile",
        resource_id=str(client.id),
        reason="client_updated",
        correlation_id=_correlation_id(request),
        metadata_json={"outcome": "updated"},
    )
    await session.commit()
    await session.refresh(client)
    return client


@router.post(
    "/{client_id}/consents",
    operation_id="recordClientConsent",
    response_model=ClientConsentResponse,
    status_code=201,
)
async def record_client_consent(
    client_id: UUID,
    payload: ClientConsentCreate,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> ClientConsent:
    """Record a consent event for a tenant-owned client."""
    await _get_client_or_404(session, context.tenant_id, client_id)
    now = datetime.now(UTC)
    consent = ClientConsent(
        tenant_id=context.tenant_id,
        client_id=client_id,
        purpose=payload.purpose,
        status=payload.status,
        consent_text_version=payload.consent_text_version,
        recorded_by_user_id=context.principal.user_id,
        granted_at=now,
        revoked_at=now if payload.status == ConsentStatus.REVOKED else None,
        expires_at=payload.expires_at,
    )
    session.add(consent)
    await session.flush()
    await AuditService(session).append(
        tenant_id=context.tenant_id,
        actor_user_id=context.principal.user_id,
        action=AuditAction.CONSENT_CHANGE,
        resource_type="client_consent",
        resource_id=str(consent.id),
        reason="consent_recorded",
        correlation_id=_correlation_id(request),
        metadata_json={"purpose": payload.purpose.value, "status": payload.status.value},
    )
    await session.commit()
    await session.refresh(consent)
    return consent


@router.get("/{client_id}/consents", operation_id="listClientConsents", response_model=ClientConsentListResponse)
async def list_client_consents(
    client_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> ClientConsentListResponse:
    """List consent records for a tenant-owned client."""
    await _get_client_or_404(session, context.tenant_id, client_id)
    consents = list(
        (
            await session.execute(
                select(ClientConsent)
                .where(ClientConsent.tenant_id == context.tenant_id, ClientConsent.client_id == client_id)
                .order_by(ClientConsent.created_at, ClientConsent.id)
            )
        )
        .scalars()
        .all()
    )
    return ClientConsentListResponse(items=[ClientConsentResponse.model_validate(consent) for consent in consents])
