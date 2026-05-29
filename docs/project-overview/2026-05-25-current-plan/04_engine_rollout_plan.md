# 04 — Engine-Rollout-Plan

## 1. Kanonische Engine-Reihenfolge

| Reihenfolge | Modul | Phase | Rolle im Gesamtsystem | Aktueller Status |
|---:|---|---|---|---|
| 1 | Radi144 | Diagnose | Resonanzmatrix, Biofield-Mapping, Confidence, Synergy Seed | erste vertikale Engine, weit fortgeschritten |
| 2 | RadiWorks | Diagnose | Raten-/Frequenz-/Entropie-Basis, Knowledge-Layer-Anbindung | geplant |
| 3 | RadiMorphic | Analyse | Multiplex/NLS/Entropy/Synergy | geplant |
| 4 | RadiBlohm | Analyse | Morphic Field, Plan-Kandidaten | geplant |
| 5 | RadiThoms | Harmonize | 5D/Meridian/Hardware-Fallback/Frequenzharmonische | geplant |
| 6 | RadiCopen | Harmonize | Copen/Level Resonance/safe Interpretation | geplant |

## 2. Radi144 Detailstatus

| Teilbereich | Status | Was ist erreicht? | Was bleibt blockiert/geplant? |
|---|---|---|---|
| Manifest / Substeps | erledigt | Inputs, Outputs, Substeps, Events, Safety im Manifest | keine offenen Manifest-Grundlagen |
| Domain Service | erledigt | deterministische Kernlogik service-seitig gekapselt | keine GPU/CUDA |
| Result Schema | erledigt | Result Contract inkl. Provenance/Retention/Client Projection | Raw-/Debugdaten bleiben verboten |
| Storage | teilweise geöffnet | `ModuleRun`, `ModuleResult`, `ModuleProvenance` | `module_projections` bleibt blockiert |
| Runtime Routes | geöffnet | klassifizierte Radi144 Runtime Routes | keine neue Projection Route ohne Gate |
| Runtime Result Write | geöffnet | Worker kann Result schreiben, Service commitet nicht intern | API-Result-Writes außerhalb Gate bleiben blockiert |
| Projection Builder | geöffnet | on-demand Projection Builder | kein Materialized Write |
| API Projection Read | geöffnet | Result → Projection on-demand | keine Materialized Projection Table |
| Worker Runtime | geöffnet | fail-closed und kontrolliert | keine externe Queue/Daemon |
| CPU-safe Execution | geöffnet | CPU-only Execution | GPU/CUDA blockiert |
| Worker Progress Events | geöffnet | Event-truth für JobTracker | keine synthetischen UI-Fortschritte |
| JobTracker Binding | geöffnet | UI liest echte Events | tiefere Engine UI später |
| Materialized Projection Planning | decision-only | Storage/Schema/Migration/ORM/Constraints dokumentiert | Implementierung noch nicht geöffnet |

## 3. Radi144 Materialized Projection Gates: aktueller Verlauf

| Reihenfolge | Gate | Status | Kernaussage |
|---:|---|---|---|
| 1 | Worker Projection Materialization Decision | erledigt | Worker Writes bleiben disabled |
| 2 | Materialized Projection Storage Decision | erledigt | Materialized Storage deferred |
| 3 | Projection Cache Policy Decision | erledigt | Cache Storage disabled |
| 4 | Storage Contract Decision | erledigt | `module_projections` als geplante Entity dokumentiert |
| 5 | Storage Schema Decision | erledigt | Storage Schema dokumentiert, keine Tabelle |
| 6 | Storage Migration Decision | erledigt | Alembic Migration disabled |
| 7 | ORM Model Decision | erledigt | `ModuleProjection` geplant, nicht implementiert |
| 8 | Relationship Contract Decision | erledigt | Tenant/Run/Result-FKs dokumentiert |
| 9 | Constraints Decision | erledigt | Constraints/Unique/Raw-Debug-Ausschlüsse dokumentiert |
| 10 | Model Enablement Decision | erledigt | Model Enablement deferred |
| 11 | ORM Implementation Decision | erledigt | ORM Implementation deferred |
| 12 | Migration Enablement Decision | erledigt | Migration Enablement deferred |
| 13 | Migration Implementation Decision | erledigt | keine Alembic Revision |
| 14 | Projection Gate Ergonomics | erledigt | Übersicht/Checkliste/Blockeranker |
| 15 | Table Creation Gate Decision | erledigt | `module_projections` geplant, aber keine Tabelle erzeugt |
| 16 | Table Contract Gate Decision | erledigt | DDL-/Table-Contract präzisiert, keine Implementierung |
| 17 | Table DDL Implementation Gate Decision | erledigt | DDL/Alembic weiterhin deferred |
| 18 | Alembic Revision Gate Decision | erledigt | Revision `0008_module_projections` reserviert, keine Datei erzeugt |
| 19 | Alembic Revision Implementation Gate Decision | erledigt | Revision-Datei geplant, aber nicht erzeugt |
| 20 | Migration File Gate Decision | erledigt | Migration-Datei weiterhin deferred |
| 21 | Migration File Contract Gate Decision | erledigt | Upgrade/Downgrade-Dateikontrakt vor Datei-Erzeugung präzisiert |
| 22 | Migration File Implementation Decision | erledigt | Datei-Erstellung bleibt deferred |
| 23 | Migration File Creation Decision | erledigt | Datei-Erzeugung bleibt deferred |
| 24 | Migration File Content Contract Decision | erledigt | Dateiinhalt vertraglich fixiert, keine Datei erzeugt |
| 25 | Migration File Authoring Decision | erledigt | Authoring bleibt deferred |
| 26 | Migration File Write Decision | erledigt | Write bleibt deferred |
| 27 | Migration File Write Implementation Decision | erledigt | Write-Implementierung bleibt deferred |
| 28 | Migration File Introduction Decision | erledigt | Repo-Einführung bleibt deferred |
| 29 | Migration File Introduction Implementation Decision | nächster Gate | entscheiden, ob Repo-Einführung implementiert werden darf |

## 4. Verbleibender Engine-Rollout nach Radi144

| Zielmodul | Voraussetzung | Erwartete Gate-Familien |
|---|---|---|
| RadiWorks | Radi144-Muster stabil, Result/Projection Pattern verstanden | Manifest → Domain Service → Result Schema → Job/API → Events → Result Storage → UI Projection |
| RadiMorphic | RadiWorks Pattern stabil | Manifest → Multiplex/NLS Contract → Domain/Service → Event/Result/Projection |
| RadiBlohm | Analyse-Pipeline stabil | Morphic Field Contract → Plan-Kandidaten → Safety/Projection |
| RadiThoms | Harmonize Safety vorbereiten | 5D/Meridian/Hardware-Fallback Contract → Approval/Runtime Boundaries |
| RadiCopen | Harmonize + Interpretation Safety | Level Resonance/Copen Contract → LLM-safe optional → Approval/Report Projection |

## 5. Engine-übergreifende spätere Ziele

| Bereich | Ziel | Voraussetzung |
|---|---|---|
| Cross-Module Synergy | mehrere Engine-Ergebnisse zusammenführen | Radi144 + mindestens weitere Engine stabil |
| Confidence / Conflict Handling | widersprüchliche Modulresultate kenntlich machen | standardisierte Result Contracts |
| Harmonization Plan | Analyse-Ergebnisse in sichere Planvorschläge überführen | Approval Gate und Claim-Safety |
| Harmonization Runtime | Live-Harmonisierung kontrolliert ausführen | Plan/Approval, Realtime, Hardware-Fallback |
| Reports | Client/Therapist-Ausgaben trennen | Projection- und Privacy-Grenzen stabil |
