# Deployment

## Clone

```bash
git clone <repo-url> /opt/radiquant-v5
cd /opt/radiquant-v5
```

## Start

```bash
docker compose -f infra/docker/docker-compose.yml up -d
```

## Health Check

```bash
curl -f http://localhost:8000/health
```

## Erster Admin-User

Lege den ersten Admin-User ueber das vorgesehene interne Bootstrap- oder Seed-Verfahren der Zielumgebung an. Setze vorher produktive Werte fuer `SECRET_KEY`, `DATABASE_URL` und die PostgreSQL-Zugangsdaten.
