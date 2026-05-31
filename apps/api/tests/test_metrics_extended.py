"""Extended Prometheus metrics tests."""

import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
import yaml
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parents[1]
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

    api = create_app()

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    api.dependency_overrides[get_db_session] = override_db_session

    try:
        yield api
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_prometheus_format(metrics_app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=metrics_app),
        base_url="http://test",
    ) as client:
        response = await client.get("/metrics/prometheus")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "# HELP" in response.text


@pytest.mark.asyncio
async def test_metrics_includes_http_requests_counter(metrics_app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=metrics_app),
        base_url="http://test",
    ) as client:
        await client.get("/metrics/")
        response = await client.get("/metrics/prometheus")

    assert response.status_code == 200
    assert "http_requests_total" in response.text


@pytest.mark.asyncio
async def test_middleware_records_request(metrics_app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=metrics_app),
        base_url="http://test",
    ) as client:
        await client.get("/metrics/")
        response = await client.get("/metrics/prometheus")

    assert 'http_requests_total{method="GET",path="/metrics/",status_code="200"}' in response.text
    assert 'http_request_duration_seconds_count{method="GET",path="/metrics/"}' in response.text


def test_slo_yml_is_valid_yaml() -> None:
    with open(REPO_ROOT / "infra/monitoring/slo.yml", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    assert sorted(slo["name"] for slo in data["slos"]) == [
        "api_availability",
        "p95_response_time_ms",
        "radi144_job_success_rate",
    ]
