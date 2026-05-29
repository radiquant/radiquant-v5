# Radi144 Materialized Projection Migration Plan — Statuspaket

**Stand:** 2026-05-27  
**Scope:** Radi144 materialized projection migration-file sub-path.  
**Nicht Scope:** Vollständige Radiquant-v5-/6-Module-Migration.

Dieses Statuspaket beschreibt den aktuellen Umsetzungsplan, abgeschlossene Gates, offene Schritte, Invarianten und prozentuale Fortschrittsabschätzungen.

## Dateien

| Datei | Zweck |
|---|---|
| `01_current_status.md` | Aktueller Zustand, letzte grüne Baseline, harte Blocker |
| `02_phase_plan.md` | Phasenplan mit erledigten und offenen Schritten |
| `03_completed_gates.md` | Chronologie der abgeschlossenen Decision-Gates |
| `04_open_roadmap.md` | Noch offene geplante Gates und spätere Implementierungsbereiche |
| `05_percentage_estimates.md` | Prozentuale Fortschrittsabschätzungen mit Gewichtung |
| `06_verification_and_invariants.md` | Verifikation, Sicherheitsgrenzen und No-Go-Invarianten |

## Aktueller Kurzstatus

- Letzter abgeschlossener Gate: `radi144_materialized_projection_migration_file_repository_file_admission_gate_decision`
- Nächster optimaler Gate: `radi144_materialized_projection_migration_file_repository_file_admission_implementation_gate_decision`
- Letzte Verifikation: `make verify` grün, `221 passed`
- `apps/api/alembic/versions/0008_module_projections.py` bleibt absent.
- `module_results.result_payload_json` bleibt Source of Truth.

## Lesart der Prozentwerte

Die Prozentwerte sind **Planungsabschätzungen**, keine Produktivfreigaben. Sie trennen bewusst zwischen:

1. **Gate-/Governance-Fortschritt** — wie weit die Absicherung und Dokumentation fortgeschritten ist.
2. **Runtime-/DB-Implementierung** — weiterhin 0% aktiviert, bis ein späterer Gate explizit öffnet.
3. **Gesamtprozess** — gewichtete Sicht über Contract, Governance, DB, ORM, Write-Service, Worker und Runtime.
