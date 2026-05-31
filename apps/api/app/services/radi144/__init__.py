"""Radi144 domain service package.

The package exposes pure, in-process primitives only. It is not wired to API
worker runtimes or engine execution.
"""

from app.services.radi144.cpu_safe_execution import (
    Radi144CpuSafeExecutionInput,
    Radi144CpuSafeExecutionService,
)
from app.services.radi144.domain import (
    Radi144ComputationPlan,
    Radi144DomainService,
    Radi144InputContext,
    Radi144ReferenceVector,
)
from app.services.radi144.job_records import Radi144JobRecordError, Radi144JobRecordService
from app.services.radi144.projection_builder import (
    Radi144ClientProjection,
    Radi144ProjectionBuilder,
    Radi144ProjectionError,
    Radi144TherapistProjection,
)
from app.services.radi144.projection_write_service import (
    ProjectionWriteError,
    ProjectionWriteResult,
    ProjectionWriteService,
)
from app.services.radi144.result_writer import Radi144ResultWriteError, Radi144ResultWriter
from app.services.radi144.worker_runtime import (
    Radi144WorkerRuntimeOutcome,
    Radi144WorkerRuntimeService,
)

__all__ = [
    "Radi144ComputationPlan",
    "Radi144DomainService",
    "Radi144CpuSafeExecutionInput",
    "Radi144CpuSafeExecutionService",
    "Radi144InputContext",
    "Radi144JobRecordError",
    "Radi144JobRecordService",
    "Radi144ReferenceVector",
    "Radi144ClientProjection",
    "Radi144ProjectionBuilder",
    "Radi144ProjectionError",
    "ProjectionWriteError",
    "ProjectionWriteResult",
    "ProjectionWriteService",
    "Radi144ResultWriteError",
    "Radi144ResultWriter",
    "Radi144TherapistProjection",
    "Radi144WorkerRuntimeOutcome",
    "Radi144WorkerRuntimeService",
]
