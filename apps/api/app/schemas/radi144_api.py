"""Radi144 non-executing runtime API DTOs.

Radi144 Engine API Runtime Route Gate scope: authenticated tenant-scoped
runtime routes that create/read job records only. They do not start workers,
write results, build projections, or execute Radi144.
"""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Radi144JobCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    workflow_run_id: UUID
    workflow_step_run_id: UUID
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=120)


Radi144JobRecordStatus = Literal["queued", "storage_ready", "result_stored", "failed_closed"]


class Radi144RuntimeRouteStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module_id: Literal["radi144"] = "radi144"
    tenant_id: UUID
    job_id: UUID | None = None
    session_id: UUID | None = None
    workflow_run_id: UUID | None = None
    workflow_step_run_id: UUID | None = None
    route_status: Literal["runtime_route_open_non_executing", "job_record_created_no_worker_runtime", "job_record_found_no_worker_runtime"] = "runtime_route_open_non_executing"
    worker_jobs_enabled: Literal[False] = False
    engine_execution_enabled: Literal[False] = False
    runtime_result_writes_enabled: Literal[False] = False
    projection_builder_enabled: Literal[False] = False
    job_status: Radi144JobRecordStatus | None = None
    result_status: Literal["blocked_until_runtime_result_writes", "not_requested"] = "not_requested"
    message: str = Field(max_length=200)
