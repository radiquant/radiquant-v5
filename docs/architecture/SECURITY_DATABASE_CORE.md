# Security Core + Database Core — Initial Gate

**Status:** Initial scaffolding and verification gates created.  
**Scope:** No product feature routes yet. Only minimal `/health` runtime route exists.

## Security Core initialized

| Gate | Status |
|---|---|
| Route Security Manifest exists | yes |
| Runtime route classification check | yes: `scripts/check_runtime_routes.py` |
| Runtime OpenAPI path drift check | yes: `scripts/check_openapi_runtime.py` |
| First public route classified | yes: `GET /health` |
| Feature routes blocked until auth/tenant/audit | yes |

## Database Core initialized as contract

| Gate | Status |
|---|---|
| Domain model contract exists | yes: `packages/contracts/domains/domain-model.v1.json` |
| MVP domains identified | identity, client, session, engine, compliance, realtime, operations |
| Data rules captured | tenant scope, consent, retention, encryption, audit, client projection |
| Actual DB migrations | not yet — next database implementation phase |

## Minimal API skeleton

| File | Purpose |
|---|---|
| `apps/api/app/main.py` | FastAPI app factory and route registration |
| `apps/api/app/routes/health.py` | Minimal public health route |
| `apps/api/app/schemas/health.py` | Pydantic schema matching OpenAPI HealthResponse |

## Current verification

`make verify` validates:

1. bootstrap skeleton,
2. planning contracts,
3. runtime FastAPI route classification,
4. runtime OpenAPI path parity with committed contract.

## Next strict order

1. Add real Auth/Tenant/Audit core contracts and models.
2. Add initial DB migration skeleton.
3. Only then implement client domain API.

No client/session/engine feature routes should be added before Auth/Tenant/Audit and DB migration gates exist.
