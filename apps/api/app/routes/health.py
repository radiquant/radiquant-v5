"""Public health route.

This is the only initial public route and is classified in the route security manifest.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.health import HealthDetailResponse

router = APIRouter(tags=["system"])


async def _has_table(session: AsyncSession, table_name: str) -> bool:
    connection = await session.connection()
    return await connection.run_sync(
        lambda sync_connection: inspect(sync_connection).has_table(table_name)
    )


async def _read_migration_head(session: AsyncSession) -> str | None:
    result = await session.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
    value = result.scalar_one_or_none()
    return str(value) if value is not None else None


@router.get(
    "/health",
    operation_id="getHealth",
    response_model=HealthDetailResponse,
    responses={503: {"model": HealthDetailResponse}},
)
async def get_health(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> HealthDetailResponse | JSONResponse:
    """Return service health and non-sensitive persistence readiness."""
    checks = {
        "select_1": False,
        "module_projections_table": False,
        "alembic_version_table": False,
    }
    try:
        await session.execute(text("SELECT 1"))
        checks["select_1"] = True
        checks["module_projections_table"] = await _has_table(session, "module_projections")
        checks["alembic_version_table"] = await _has_table(session, "alembic_version")
        migration_head = (
            await _read_migration_head(session) if checks["alembic_version_table"] else None
        )
    except Exception:
        response = HealthDetailResponse(
            status="unhealthy",
            db="error",
            migration_head=None,
            checks=checks,
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response.model_dump(),
        )

    health_status = "ok" if all(checks.values()) else "degraded"
    return HealthDetailResponse(
        status=health_status,
        db="ok",
        migration_head=migration_head,
        checks=checks,
    )
