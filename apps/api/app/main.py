"""radiquant-v5 FastAPI application entrypoint.

Current scope: minimal contract-bound API skeleton only. Feature routes remain blocked
until Security Core, Database Core, and route governance gates are implemented.
"""

from fastapi import FastAPI

from app.middleware.metrics_middleware import MetricsMiddleware
from app.routes.admin import admin_router
from app.routes.auth import router as auth_router
from app.routes.clients import router as clients_router
from app.routes.gdpr import gdpr_router
from app.routes.harmonization import harmonization_router
from app.routes.health import router as health_router
from app.routes.llm_copilot import llm_copilot_router
from app.routes.metrics import metrics_router
from app.routes.radi144 import router as radi144_router
from app.routes.radiblohm import router as radiblohm_router
from app.routes.radicopen import router as radicopen_router
from app.routes.radimorphic import router as radimorphic_router
from app.routes.radithoms import router as radithoms_router
from app.routes.radiworks import router as radiworks_router
from app.routes.realtime import router as realtime_router
from app.routes.reports import reports_router
from app.routes.sessions import router as sessions_router
from app.routes.workflows import router as workflows_router

APP_VERSION = "0.0.0"


def create_app() -> FastAPI:
    """Create the FastAPI application with only contract-classified routes."""
    app = FastAPI(
        title="radiquant-v5 API",
        version=APP_VERSION,
        description="Controlled ground-zero rebuild API skeleton.",
        openapi_version="3.1.0",
    )
    app.add_middleware(MetricsMiddleware)
    app.include_router(health_router)
    app.include_router(admin_router)
    app.include_router(auth_router)
    app.include_router(clients_router)
    app.include_router(gdpr_router)
    app.include_router(sessions_router)
    app.include_router(harmonization_router)
    app.include_router(llm_copilot_router)
    app.include_router(workflows_router)
    app.include_router(realtime_router)
    app.include_router(radi144_router)
    app.include_router(reports_router)
    app.include_router(metrics_router)
    app.include_router(radiworks_router, prefix="/api/v1")
    app.include_router(radimorphic_router, prefix="/api/v1")
    app.include_router(radiblohm_router, prefix="/api/v1")
    app.include_router(radithoms_router, prefix="/api/v1")
    app.include_router(radicopen_router, prefix="/api/v1")
    return app


app = create_app()
