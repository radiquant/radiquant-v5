# 02 — Bisher erarbeitete Gates

## 1. Foundation- und Plattform-Gates

| Reihenfolge | Gate / Bereich | Status | Ergebnis |
|---:|---|---|---|
| 1 | Basisordner / Restart Skeleton | erledigt | `/opt/radiquant-v5` kontrolliert aufgebaut |
| 2 | Tooling / Verify Pipeline | erledigt | `make verify` als Hauptgate etabliert |
| 3 | Contract Foundation | erledigt | OpenAPI, Route Security, Workflow/Event Contracts vorhanden |
| 4 | Runtime Security Core | erledigt | negative Security-Tests vorhanden |
| 5 | Identity / Auth / Tenant / Audit Core | erledigt | Login, Tenant, Rollen, Audit-Basis vorhanden |
| 6 | DB Core | erledigt | Identity/Tenant/Audit/Client/Session-Grundlagen migriert |
| 7 | Frontend Shell | erledigt | Login/Dashboard/Design Tokens, contract-bound |
| 8 | Client Domain API | erledigt | Client Create/List/Detail/Consent-Pfade vorhanden |
| 9 | Client Frontend Gate | erledigt | UI für Client-Grundlagen vorhanden |
| 10 | Consent Domain Gate | erledigt | Consent Gate und Tests vorhanden |
| 11 | Session Domain Gate | erledigt | Session-Grundlagen vorhanden |
| 12 | Workflow Manifest Gate | erledigt | Workflow Manifest v2 validiert |
| 13 | Workflow API Gate | erledigt | Workflow API und Step-Erzeugung vorhanden |
| 14 | Event Schema Gate | erledigt | Event Envelope / Registry validiert |
| 15 | Realtime API Gate | erledigt | SSE/Event-Replay-Pfad vorhanden |
| 16 | JobTracker UI Gate | erledigt | JobTracker-Shell mit Connection States |

## 2. Radi144 Engine- und Result-Gates

| Reihenfolge | Gate | Status | Ergebnis / Grenze |
|---:|---|---|---|
| 17 | Radi144 Engine Manifest Gate | erledigt | Radi144 als erste vertikale Engine manifestiert |
| 18 | Radi144 Domain Service Gate | erledigt | deterministische Domain-Logik, keine Runtime-/DB-Öffnung |
| 19 | Radi144 Result Schema Gate | erledigt | Result Contract mit Provenance, Retention, Client Projection |
| 20 | Radi144 Result Persistence Gate Decision | erledigt | Persistenz zunächst bewusst entschieden/gegated |
| 21 | Radi144 Engine Job Gate Decision | erledigt | Job Contract, Execution noch getrennt |
| 22 | Radi144 Engine API Gate Decision | erledigt | API Boundary dokumentiert |
| 23 | Radi144 Client Projection Gate Decision | erledigt | Client/Therapist Projection-Grenze dokumentiert |
| 24 | Radi144 Result Persistence Storage Gate | erledigt | `ModuleRun`, `ModuleResult`, `ModuleProvenance` Storage |
| 25 | Radi144 Engine API Runtime Route Gate | erledigt | klassifizierte Runtime Routes, OpenAPI-backed |
| 26 | Radi144 Runtime Result Write Gate | erledigt | `Radi144ResultWriter.persist_result`, kein interner Commit |
| 27 | Radi144 Projection Builder Gate | erledigt | Service-only Projection Builder |
| 28 | Radi144 API Projection Read Gate | erledigt | on-demand Projection aus Result Payload |

## 3. Radi144 Worker-/Execution-/Event-Gates

| Reihenfolge | Gate | Status | Ergebnis / Grenze |
|---:|---|---|---|
| 29 | Radi144 Worker Job Gate | erledigt | Worker Job Boundary dokumentiert |
| 30 | Radi144 Worker Runtime Gate | erledigt | Runtime fail-closed vorbereitet |
| 31 | Radi144 Engine Execution Gate Decision | erledigt | konservative Execution-Entscheidung |
| 32 | Radi144 CPU-safe Execution Gate | erledigt | CPU-only Execution Service geöffnet |
| 33 | Radi144 Worker CPU Execution Wiring Gate | erledigt | Worker darf CPU-safe Service ausführen |
| 34 | Radi144 Worker Progress Event Gate | erledigt | Fortschritt als Event-truth |
| 35 | Radi144 JobTracker Event Binding Gate | erledigt | JobTracker zeigt echte Radi144 Events |
| 36 | Radi144 External Queue Decision Gate | erledigt | externe Queue/Daemon bleibt disabled |

## 4. Radi144 Materialized Projection Decision-Kette

| Reihenfolge | Gate | Status | Ergebnis / Grenze |
|---:|---|---|---|
| 37 | Worker Projection Materialization Decision | erledigt | Worker Projection Writes bleiben disabled |
| 38 | Materialized Projection Storage Decision | erledigt | Storage bleibt disabled |
| 39 | Projection Cache Policy Decision | erledigt | Cache Policy dokumentiert, Cache Storage disabled |
| 40 | Storage Contract Decision | erledigt | geplante Entity `module_projections` dokumentiert |
| 41 | Storage Schema Decision | erledigt | Schema dokumentiert, keine Implementierung |
| 42 | Storage Migration Decision | erledigt | Alembic Revision bleibt disabled |
| 43 | ORM Model Decision | erledigt | `ModuleProjection` geplant, aber disabled |
| 44 | Relationship Contract Decision | erledigt | FK-Beziehungen dokumentiert |
| 45 | Constraints Decision | erledigt | Tenant/Role/Hash/Unique/Raw-Debug-Ausschlüsse dokumentiert |
| 46 | Model Enablement Decision | erledigt | Model Enablement deferred |
| 47 | ORM Implementation Decision | erledigt | ORM Implementation deferred |
| 48 | Migration Enablement Decision | erledigt | Migration Enablement deferred |
| 49 | Migration Implementation Decision | erledigt | keine Alembic Revision, weiter deferred |
| 50 | Projection Gate Ergonomics | erledigt | Checkliste, Statusanker, Blockerübersicht |
| 51 | Table Creation Decision | erledigt | `module_projections` als geplante Tabelle bestätigt, Tabelle bleibt disabled |
| 52 | Table Contract Decision | erledigt | Spalten/FKs/Constraints/Indizes dokumentiert, DDL bleibt disabled |
| 53 | Table DDL Implementation Decision | erledigt | DDL/Alembic bleibt deferred bis Alembic Revision Gate |
| 54 | Alembic Revision Decision | erledigt | Revision `0008_module_projections` reserviert, keine Datei erzeugt |
| 55 | Alembic Revision Implementation Decision | erledigt | Datei `0008_module_projections.py` geplant, aber nicht erzeugt |
| 56 | Migration File Decision | erledigt | Migration-Datei bleibt deferred bis File Contract Gate |
| 57 | Migration File Contract Decision | erledigt | Upgrade-/Downgrade-Dateikontrakt dokumentiert, Datei bleibt deferred |
| 58 | Migration File Implementation Decision | erledigt | Implementierungsentscheidung dokumentiert, Datei bleibt absent |
| 59 | Migration File Creation Decision | erledigt | Datei-Erzeugung bleibt bis Content-Contract-Gate deferred |
| 60 | Migration File Content Contract Decision | erledigt | exakter zukünftiger Dateiinhalt dokumentiert, Datei bleibt absent |
| 61 | Migration File Authoring Decision | erledigt | Authoring bleibt bis Write-Gate deferred |
| 62 | Migration File Write Decision | erledigt | Datei-Write bleibt bis Write-Implementation-Gate deferred |
| 63 | Migration File Write Implementation Decision | erledigt | Write-Implementation bleibt bis Introduction-Gate deferred |
| 64 | Migration File Introduction Decision | erledigt | Repo-Einführung bleibt bis Introduction-Implementation-Gate deferred |

## 5. Aktuelle Artefaktfamilien

| Artefaktfamilie | Beispiele | Rolle |
|---|---|---|
| Contracts | `packages/contracts/**` | Contract-first SSOT für APIs, Events, Jobs, Projections |
| Validators | `scripts/check_*.py`, `scripts/validate_contracts.py` | Gate- und Drift-Prüfung |
| Tests | `tests/test_*.py` | Regression und Gate-Sicherung |
| Architecture Docs | `docs/architecture/*.md` | Entscheidung, Grenze, Akzeptanzkriterien |
| Project Anchors | `docs/pi/project.yml` | aktueller Projektzustand und Next Phase |
| Runtime Code | `apps/api/app/**`, `apps/web-astro/**` | nur in explizit geöffneten Scopes |

## 6. Stabilitätsstand nach letzter Prüfung

| Metrik | Wert |
|---|---:|
| Pytest | `177 passed` |
| Runtime Routes | `20 classified` |
| Runtime OpenAPI Paths | `15` |
| LSP Diagnostics | `0 errors` |
| Nächster Gate | `radi144_materialized_projection_migration_file_contract_gate_decision` |
