# START HERE — radiquant-v5

This repository is the clean target workspace for the controlled radiquant-v5 rebuild.

## Source of truth

The detailed planning source remains in the radiquant4 reference repository until copied/converted into executable v5 contracts:

- `/opt/radiquant4/docs/pi/`
- `/opt/radiquant4/docs/restart-radiquant-v5/`
- `/opt/radiquant4/docs/audits/2026-05-22_codebase_deep_analysis/`

## Confirmed decisions

| Decision | Value |
|---|---|
| Backend | FastAPI / Python |
| Frontend | Astro SSR + React Islands |
| DB | PostgreSQL |
| Redis | cache, queue, streams/events, locks |
| First engine | Radi144 |
| MVP | Core + Client + Session + Workflow Manifest + Radi144 vertical slice |
| Workflow taxonomy | W-A Schnell-Diagnose, W-B Vollanalyse, W-C Gruppenanalyse, W-D Verlauf, W-E Harmonisierung, W-F Direktmodul, W-L Labs |

## Hard invariants

| Invariant | Meaning |
|---|---|
| No unclassified route | Every API route must be public/auth/tenant/admin/internal. |
| No frontend URL without contract | Frontend may only call generated/central contract clients. |
| No workflow step outside manifest | UI steps/substeps must come from Workflow Manifest v2. |
| No client raw debug data | Client projection excludes raw engine/admin/debug output. |
| No sensitive plaintext in production | Sensitive blobs require encryption and no fallback. |
| No realtime without fallback | SSE/WebSocket/WebTransport requires reconnect and fallback. |
| No innovation without flag | HRV, Quantum, LLM, Labs are feature-flagged. |
| No medical healing claims | All UI/report/LLM language remains wellbeing-oriented. |

## Next implementation phase

Proceed with Phase 2 from `/opt/radiquant4/docs/restart-radiquant-v5/08_OPTIMAL_REBUILD_SEQUENCE.md`:

1. Tooling and standards.
2. Version pinning.
3. Verify command.
4. CI placeholders.
5. Contract foundation placeholders.

Do not start feature implementation before those gates exist.
