"""Minimal public health route.

This is the only initial public route and is classified in the route security manifest.
"""

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", operation_id="getHealth", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Return minimal service health without sensitive metadata."""
    return HealthResponse(status="ok", service="radiquant-v5-api", version="0.0.0")
