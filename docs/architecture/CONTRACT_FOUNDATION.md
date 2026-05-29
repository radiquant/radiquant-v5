# Contract Foundation — radiquant-v5

**Phase:** 3 from the optimal rebuild sequence.  
**Status:** Initial planning contracts created before feature implementation.

## Created contracts

| Contract | Path | Purpose |
|---|---|---|
| OpenAPI placeholder | `packages/contracts/openapi/openapi.v1.json` | Minimal `/health` contract; later replaced by FastAPI runtime export. |
| Workflow Manifest v2 | `packages/contracts/workflows/workflow-manifest.v2.json` | Confirmed W-A to W-L taxonomy, 6 modules, Radi144 first vertical slice. |
| Event Registry v1 | `packages/contracts/events/event-registry.v1.json` | Event families, connection states, job states, security invariants. |
| Route Security Manifest v1 | `packages/contracts/routes/route-security-manifest.v1.json` | Initial `/health` route classification and planned route group rules. |
| Contract Schemas | `packages/contracts/schemas/*.schema.json` | Document expected structure; verified by custom stdlib validator. |

## Verification

`make verify` now validates:

1. bootstrap skeleton,
2. canonical radiquant4 reference docs,
3. contract files exist and parse,
4. workflow taxonomy contains W-A to W-L,
5. all six engine modules exist,
6. Radi144 is the first vertical slice,
7. OpenAPI `/health` is classified in the route manifest,
8. event registry forbids tokens in URLs.

## Next phase

After this foundation, continue with Phase 4 / Security Core and Phase 5 / Database Core only after deciding whether to scaffold API first or contract tests first. No feature code should bypass these contracts.
