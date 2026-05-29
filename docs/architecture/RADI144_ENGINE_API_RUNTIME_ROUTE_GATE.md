# Radi144 Engine API Runtime Route Gate

Status: runtime routes open non-executing.

## Decision

The Radi144 Engine API runtime route gate opens the previously planned tenant-scoped API paths as **non-executing** runtime routes.

Opened paths:

- `POST /engines/radi144/jobs`
- `GET /engines/radi144/jobs/{job_id}`
- `GET /engines/radi144/jobs/{job_id}/result`

These routes are authenticated, tenant-classified, and present in both the route security manifest and committed OpenAPI contract.

## Non-execution boundary

The routes only return boundary/status responses. They do not enqueue workers, execute Radi144, write module results, read result payloads, or build projections.

runtime result writes remain blocked.
worker jobs remain blocked.
engine execution remains blocked.
projection builder remains blocked.

## Safety invariants

- Tenant context is required.
- Tokens in URLs remain forbidden.
- No worker job is created.
- No runtime result writes occur.
- No projection builder runs.
- No medical/healing claims are exposed.

## Next gate

The next optimal gate is `radi144_runtime_result_write_gate_decision`.

Reason: storage exists and non-executing routes are now classified. A later gate can decide whether runtime writes are allowed, still without enabling engine execution or worker jobs unless explicitly opened.

## Verification

Run:

```bash
make verify
```

The verification chain checks runtime route classification, OpenAPI path parity, and continued blockers for runtime result writes, workers, projection builder, and execution.
