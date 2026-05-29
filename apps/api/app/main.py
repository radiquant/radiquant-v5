"""radiquant-v5 FastAPI application entrypoint.

Current scope: minimal contract-bound API skeleton only. Feature routes remain blocked
until Security Core, Database Core, and route governance gates are implemented.
"""

from fastapi import FastAPI

from app.routes.auth import router as auth_router
from app.routes.clients import router as clients_router
from app.routes.health import router as health_router
from app.routes.radi144 import router as radi144_router
from app.routes.realtime import router as realtime_router
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
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(clients_router)
    app.include_router(sessions_router)
    app.include_router(workflows_router)
    app.include_router(realtime_router)
    app.include_router(radi144_router)
    return app


app = create_app()
