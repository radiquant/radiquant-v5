FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt ./

RUN python -m pip install --upgrade pip \
    && python -m pip install --prefix=/install -r requirements.txt


FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/apps/api

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY apps/api /app/apps/api
COPY apps/api/alembic.ini /app/apps/api/alembic.ini

WORKDIR /app/apps/api

USER appuser

EXPOSE 8000

ENTRYPOINT ["sh", "-c", "cd /app && alembic -c apps/api/alembic.ini upgrade head && cd /app/apps/api && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
