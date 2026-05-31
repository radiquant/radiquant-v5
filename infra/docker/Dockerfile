FROM python:3.11-slim AS builder

WORKDIR /build

COPY pyproject.toml ./

RUN python - <<'PY' > requirements.txt
import tomllib

with open("pyproject.toml", "rb") as handle:
    project = tomllib.load(handle)["project"]

for dependency in project["dependencies"]:
    print(dependency)
PY

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

WORKDIR /app/apps/api

USER appuser

EXPOSE 8000

ENTRYPOINT ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
