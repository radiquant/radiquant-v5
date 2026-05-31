"""Prometheus metrics route tests."""

import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

import app.models  # noqa: F401, E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db_session, make_async_engine  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest_asyncio.fixture
async def metrics_app() -> AsyncIterator[FastAPI]:
    engine = make_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    app = create_app()

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db_session

    try:
        yield app
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_metrics_returns_prometheus_format(metrics_app: FastAPI) -> None:
    transport = ASGITransport(app=metrics_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/metrics/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert "# HELP radiquant_sessions_total Total sessions" in body
    assert "# TYPE radiquant_sessions_total counter" in body
    assert "radiquant_sessions_total 0" in body
    assert "# HELP radiquant_clients_total Total clients" in body
    assert "# TYPE radiquant_clients_total gauge" in body
    assert "radiquant_clients_total 0" in body
