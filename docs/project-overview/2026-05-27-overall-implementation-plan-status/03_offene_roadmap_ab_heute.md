# 03 — Offene Roadmap ab heutigem Stand

## Direkt nächster Schritt

`radi144_materialized_projection_migration_file_repository_file_admission_implementation_gate_decision`

Ziel:

- Acceptance-Gate als decision-only Contract ergänzen.
- Keine Alembic-Datei erzeugen.
- Keine Tabelle, kein ORM, kein Write Service, kein Worker, keine Route öffnen.
- Danach `make verify` und Pytest grün halten.

## Kurzfristige offene Schritte im aktuellen Subpfad

| Reihenfolge | Schritt | Erwartung |
|---:|---|---|
| 1 | Acceptance Decision | deferred, keine Datei |
| 2 | Acceptance Implementation Decision | deferred, keine Datei |
| 3 | Admission/Merge Decision | deferred, keine Datei |
| 4 | Admission/Merge Implementation Decision | deferred, keine Datei |
| 5 | Expliziter File-Unlock Gate | nur falls bewusst erlaubt |
| 6 | Alembic File Creation | erst nach Unlock |

## Danach: tatsächliche materialisierte Projection

Erst nach expliziter Freigabe:

1. Alembic-Datei `0008_module_projections.py`
2. Tabelle `module_projections`
3. Tenant-scoped Indizes und Constraints
4. ORM-Modell `ModuleProjection`
5. Projection Write Service
6. Worker Projection Materialization
7. Idempotenter Backfill
8. Monitoring/Runbook
9. Optional neue Runtime Route mit OpenAPI + Route-Security Manifest

## Danach: zurück in den Gesamtplan

Sobald Radi144 als Musterpfad stabil ist:

- Phase 14 Minimal Admin/Ops vertiefen
- Phase 15 Engine Rollout 2–6 beginnen
- Phase 16 Synergy Merge vorbereiten
- Phase 17–18 Harmonization Plan/Job erst nach Safety-/Approval-Gates
- Phase 20 Reports/Exports erst nach stabilen Projection Boundaries
- Phase 21 GDPR/Retention/Backup produktionsreif machen
- Phase 23 Full Verification Pipeline finalisieren
- Phase 24 Deployment Baseline herstellen

## Entscheidende Reihenfolge

Die optimale Reihenfolge bleibt:

1. Stabiler Radi144 Musterpfad
2. Saubere Result-/Projection-Grenzen
3. Materialisierte Projection nur nach expliziter Öffnung
4. Dann Engine-Rollout 2–6
5. Dann Synergy/Harmonization/Reports/Ops

## Risiko, wenn man abkürzt

Ein Überspringen der Gates würde riskieren:

- Contract Drift
- Tenant-Isolation-Lücken
- falsche Source-of-Truth-Logik
- unklare Rollbacks
- raw/debug Daten in Projection Storage
- API-Routen ohne Security Manifest
- Worker-Materialisierung ohne Idempotenz

Deshalb ist der aktuelle langsame Gate-Pfad architektonisch sinnvoll.
