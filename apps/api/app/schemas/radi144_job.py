"""Radi144 engine job contract DTOs.

These models describe the job lifecycle boundary only. They do not enqueue
workers, expose routes, persist results, or execute Radi144.
"""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Radi144JobStatus = Literal[
    "queued",
    "running",
    "waiting_for_hardware",
    "paused",
    "reconnecting",
    "fallback_polling",
    "completed",
    "failed",
    "cancelled",
]
Radi144JobEvent = Literal[
    "job.queued",
    "job.running",
    "job.paused",
    "job.resumed",
    "job.cancelled",
    "job.done",
    "job.failed",
    "module.radi144.started",
    "module.radi144.completed",
    "module.radi144.failed",
    "substep.started",
    "substep.progress",
    "substep.output.ready",
    "substep.completed",
    "substep.failed",
]


class Radi144JobTimeoutPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["radi144_engine_manifest_substeps"] = "radi144_engine_manifest_substeps"
    max_total_timeout_s: int = Field(gt=0, le=900)
    fail_closed: Literal[True] = True


class Radi144JobFallbackPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    missing_input: Literal["fail_closed_no_partial_result"] = "fail_closed_no_partial_result"
    hardware_unavailable: Literal["cpu_plan_or_fail_closed"] = "cpu_plan_or_fail_closed"
    partial_result_allowed: Literal[False] = False
    synthetic_result_allowed: Literal[False] = False


class Radi144EngineJobContract(BaseModel):
    """Contract-only Radi144 job descriptor; not a runtime worker job."""

    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["radi144_engine_job_v1"] = "radi144_engine_job_v1"
    job_id: UUID
    tenant_id: UUID
    session_id: UUID
    workflow_run_id: UUID
    workflow_step_run_id: UUID
    module_id: Literal["radi144"] = "radi144"
    phase: Literal["diagnose"] = "diagnose"
    job_kind: Literal["engine_module_contract_only"] = "engine_module_contract_only"
    status: Radi144JobStatus
    worker_runtime_enabled: Literal[False] = False
    engine_execution_enabled: Literal[False] = False
    api_exposure: Literal["blocked_until_engine_api_gate"] = "blocked_until_engine_api_gate"
    result_persistence: Literal["blocked_until_result_persistence_gate"] = "blocked_until_result_persistence_gate"
    client_projection: Literal["blocked_until_client_projection_gate"] = "blocked_until_client_projection_gate"
    allowed_events: list[Radi144JobEvent] = Field(min_length=8)
    timeout_policy: Radi144JobTimeoutPolicy
    fallback_policy: Radi144JobFallbackPolicy
