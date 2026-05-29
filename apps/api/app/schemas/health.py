"""Health response schema matching the OpenAPI contract."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Minimal public health response.

    Must not expose tenant data, secrets, internal topology, or sensitive metadata.
    """

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "degraded", "fail"]
    service: Literal["radiquant-v5-api"]
    version: str
