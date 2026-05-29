# Radiquant v5 — Aktueller Gesamtüberblick

**Stand:** 2026-05-25  
**Zweck:** Leicht nachvollziehbare, tabellarische Übersicht über den aktuellen Stand des kontrollierten Neuaufbaus und den noch vorgesehenen Gesamtplan.  
**Leitlinie:** Contract-first, Security-by-default, Tenant-first, Consent-aware, Event-truth, Wellbeing-only.

## Inhalt

| Datei | Zweck |
|---|---|
| [`01_aktueller_status.md`](01_aktueller_status.md) | Kompakter Status: was geöffnet, stabil, blockiert und als nächstes geplant ist. |
| [`02_erarbeitete_gates.md`](02_erarbeitete_gates.md) | Tabellarische Liste aller bisher erarbeiteten Gates und Artefakte. |
| [`03_gesamt_umsetzungsplan.md`](03_gesamt_umsetzungsplan.md) | Gesamtplan aus der optimalen Rebuild-Sequenz mit aktuellem Fortschrittsstatus. |
| [`04_engine_rollout_plan.md`](04_engine_rollout_plan.md) | Engine-Reihenfolge, Radi144-Status und verbleibender Rollout für RadiWorks bis RadiCopen. |
| [`05_blocker_next_steps.md`](05_blocker_next_steps.md) | Blockierte Scopes, harte Stop-Regeln und nächste optimale Schritte. |

## Aktueller nächster Gate

| Feld | Wert |
|---|---|
| Nächster Gate | `radi144_materialized_projection_migration_file_repository_file_admission_implementation_gate_decision` |
| Code Features erlaubt | `false` |
| Sicherheitsmodus | Decision-/Contract-first, keine Runtime-Öffnung ohne expliziten Gate |
| Aktuelle Verifikation | `make verify` grün, `196 passed`, Runtime Routes `20`, OpenAPI Paths `15` |

## Wichtigste Sicherheitsgrenze

Die Materialized-Projection-Strecke ist bewusst vorbereitet, aber noch nicht geöffnet. Weiterhin blockiert bleiben insbesondere:

- Alembic Projection Migration
- `module_projections` DB Table
- Materialized Projection ORM Model
- Projection Write Service
- Worker Projection Materialization
- neue Projection Runtime Route
- GPU/CUDA Execution
- API-triggered Execution
- externe Queue/Daemon Execution
