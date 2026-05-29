"""Workflow API Gate request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.workflow import WorkflowRunStatus, WorkflowStepRunStatus


class WorkflowRunCreateRequest(BaseModel):
    """Request a manifest-derived workflow plan for an active session."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(min_length=1, max_length=16, pattern=r"^W-[A-Z]$")


class WorkflowStepRunResponse(BaseModel):
    """Safe workflow step projection without engine execution state."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    workflow_run_id: UUID
    step_index: int
    module_id: str
    phase: str
    status: WorkflowStepRunStatus
    created_at: datetime
    updated_at: datetime


class WorkflowRunResponse(BaseModel):
    """Safe workflow run projection derived only from the manifest."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    session_id: UUID
    workflow_id: str
    workflow_slug: str
    status: WorkflowRunStatus
    created_at: datetime
    updated_at: datetime
    steps: list[WorkflowStepRunResponse]


class WorkflowRunListResponse(BaseModel):
    """List response for tenant-scoped workflow runs."""

    model_config = ConfigDict(extra="forbid")

    items: list[WorkflowRunResponse]
    limit: int
    offset: int
