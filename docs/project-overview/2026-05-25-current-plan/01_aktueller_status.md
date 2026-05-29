# 01 — Aktueller Status

## 1. Gesamtstatus in Kurzform

| Bereich | Aktueller Stand | Stabilitätsgrad | Bemerkung |
|---|---:|---|---|
| Projektbasis `/opt/radiquant-v5` | aufgebaut | stabil | eigener v5-Projektraum mit Verify-Pipeline |
| Tooling / Verify | aktiv | stabil | `make verify` ist aktueller Hauptgate |
| Contract Foundation | umgesetzt | stabil | OpenAPI, Route Security, Workflow/Event Contracts validieren |
| Security / Tenant / Audit Core | umgesetzt | stabil | Route-Klassen, Tenant Guards, Audit-Basis vorhanden |
| Client / Consent / Session Core | umgesetzt | stabil | Client-, Consent- und Session-Grundlagen vorhanden |
| Workflow API / Event Schema / Realtime | umgesetzt | stabil | WorkflowRun/Steps, Events und SSE/Event-Replay vorhanden |
| Frontend Shell / JobTracker Basis | umgesetzt | stabil | contract-bound, keine Fake-URLs, JobTracker Event Binding vorhanden |
| Radi144 Backend Vertical | weit fortgeschritten | stabil, aber bewusst gegated | CPU-safe Worker-Execution, Result Write, Projection Read vorhanden |
| Radi144 Materialized Projection Storage | vorbereitet | decision-only | Storage/Schema/Migration/ORM/Constraints geplant, aber nicht geöffnet |
| Weitere Engines 2–6 | vorgesehen | noch nicht tief umgesetzt | RadiWorks bis RadiCopen folgen nach stabilem Muster |
| Admin/Ops, Reports, GDPR, Deployment, Labs | vorgesehen | geplant | spätere globale Planphasen |

## 2. Aktuelle Verifikation

| Check | Ergebnis |
|---|---:|
| `make verify` | grün |
| Pytest | `177 passed` |
| Runtime Routes | `20 classified` |
| Runtime OpenAPI Paths | `15` |
| LSP Diagnostics zuletzt | `0 errors` |

## 3. Aktuell geöffnete Scopes

| Scope | Status | Grenze |
|---|---|---|
| Radi144 Engine Manifest | geöffnet | Contract-/Manifest-Basis |
| Radi144 Domain Service | geöffnet | deterministische CPU-/Service-Logik, keine DB-Commits |
| Radi144 Result Schema | geöffnet | Result Contract mit Client Projection und Retention |
| Radi144 Result Persistence Storage | geöffnet | `ModuleRun`, `ModuleResult`, `ModuleProvenance` |
| Radi144 Runtime Result Write Service | geöffnet | Service-only, `persist_result` commitet nicht intern |
| Radi144 Projection Builder | geöffnet | Service-only, on-demand Projection |
| Radi144 API Projection Read | geöffnet | liest aus `module_results.result_payload_json` und baut Projection on-demand |
| Radi144 Worker Runtime | geöffnet | kontrolliert, fail-closed, tenant-/workflow-guarded |
| Radi144 CPU-safe Execution | geöffnet | CPU-only, kein GPU/CUDA |
| Radi144 Worker CPU Execution Wiring | geöffnet | Worker darf CPU-safe Service nutzen und Result schreiben |
| Radi144 Worker Progress Events | geöffnet | Event-truth für Fortschritt |
| JobTracker Event Binding | geöffnet | UI liest echte Events aus `/sessions/{session_id}/events` |

## 4. Aktuell blockierte Scopes

| Blockierter Scope | Status | Grund |
|---|---|---|
| GPU/CUDA Execution | blockiert | braucht eigenen Execution-Gate |
| API-triggered Execution außerhalb freigegebener Pfade | blockiert | kein unkontrolliertes Engine-Starten |
| externe Queue / Daemon Execution | blockiert | External Queue Decision = no-go/deferred |
| Worker Projection Materialization | blockiert | Projektionen bleiben on-demand |
| Materialized Projection Storage Writes | blockiert | keine Materialized Copy ohne explizite Gate-Kette |
| `module_projections` DB Table | blockiert | Table Creation Gate noch nicht geöffnet |
| SQLAlchemy `ModuleProjection` ORM Model | blockiert | ORM Model bleibt deferred |
| Alembic Projection Migration | blockiert | keine Revision/Tabelle bisher |
| Projection Write Service | blockiert | keine persistierte Projection-Copy |
| neue Projection Runtime Route | blockiert | keine neue Route ohne OpenAPI/Route-Security-Gate |
| Raw-/Debug-/Internal Projection Storage | blockiert | Datenschutz-/Client-Projection-Grenze |

## 5. Aktueller nächster Gate

| Feld | Wert |
|---|---|
| Nächste Phase | `radi144_materialized_projection_migration_file_repository_file_admission_implementation_gate_decision` |
| Code Features erlaubt | `false` |
| Erwartete Arbeitsweise | Decision-only / Contract-first |
| Darf Tabelle erzeugt werden? | Nein, Table Creation ist weiterhin nur als Decision dokumentiert |
| Darf ORM Model erzeugt werden? | Nein |
| Darf Write Service erzeugt werden? | Nein |
| Darf Worker materialisieren? | Nein |

## 6. Aktuelle Single Source of Truth

| Thema | SSOT |
|---|---|
| Projektphase / nächster Gate | `docs/pi/project.yml` |
| Radi144 Runtime Scope | `packages/contracts/engines/radi144.engine-manifest.v1.json` |
| API Runtime Contract | `packages/contracts/openapi/openapi.v1.json` |
| Route-Klassen | `packages/contracts/routes/route-security-manifest.v1.json` |
| Workflow/Module | `packages/contracts/workflows/workflow-manifest.v2.json` |
| Event Registry | `packages/contracts/events/event-registry.v1.json` |
| Ergonomie-Checkliste | `docs/architecture/RADI144_PROJECTION_GATE_ERGONOMICS.md` |
