"""Prometheus HTTP metrics middleware."""

from __future__ import annotations

import time

from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests by method, path, and status code.",
    ["method", "path", "status_code"],
)
HTTP_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration by method and path.",
    ["method", "path"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record per-request Prometheus metrics."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        HTTP_REQUESTS.labels(
            method=request.method,
            path=request.url.path,
            status_code=str(response.status_code),
        ).inc()
        HTTP_DURATION.labels(
            method=request.method,
            path=request.url.path,
        ).observe(duration)
        return response
