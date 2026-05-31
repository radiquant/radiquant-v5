"""Prometheus metrics route."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.client import ClientProfile
from app.models.session import ClientSession

metrics_router = APIRouter(prefix="/metrics", tags=["metrics"])


@metrics_router.get("/", operation_id="getPrometheusMetrics", response_class=PlainTextResponse)
async def get_metrics(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PlainTextResponse:
    """Return public aggregate metrics in Prometheus text format."""
    sessions_total = await session.scalar(select(func.count()).select_from(ClientSession))
    clients_total = await session.scalar(select(func.count()).select_from(ClientProfile))
    content = "\n".join(
        [
            "# HELP radiquant_sessions_total Total sessions",
            "# TYPE radiquant_sessions_total counter",
            f"radiquant_sessions_total {int(sessions_total or 0)}",
            "# HELP radiquant_clients_total Total clients",
            "# TYPE radiquant_clients_total gauge",
            f"radiquant_clients_total {int(clients_total or 0)}",
            "",
        ]
    )
    return PlainTextResponse(content=content, media_type="text/plain")


@metrics_router.get("/prometheus", operation_id="getPrometheusClientMetrics")
async def get_prometheus_client_metrics() -> Response:
    """Return process and middleware metrics from the Prometheus client registry."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
