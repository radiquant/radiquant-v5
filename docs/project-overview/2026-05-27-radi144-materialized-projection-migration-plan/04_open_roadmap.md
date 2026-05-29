# 04 — Offene Roadmap

## Sofort nächster Schritt

1. `radi144_materialized_projection_migration_file_repository_file_admission_implementation_gate_decision`
   - Zweck: Entscheidung dokumentieren, ob die Repo-Datei-Admission-Implementierung vorbereitet werden darf.
   - Erwartetes Ergebnis im aktuellen Sicherheitsmodus: weiterhin deferred, keine Datei.
   - Verifikation: neuer Validator + Test + Manifest-/Bootstrap-Registrierung + `make verify`.

## Kurzfristig geplante Governance-Gates

Diese Gates sind als nächste naheliegende Decision-only-Fortsetzung vorgesehen. Die genaue Sequenz kann bei neuem Risiko- oder Architekturentscheid angepasst werden.

| Priorität | Geplanter Gate | Erwarteter Modus |
|---:|---|---|
| 1 | Admission Implementation | decision-only, deferred |
| 2 | Post-Admission Decision | decision-only, deferred |
| 4 | Merge/Admission Follow-up Decision | decision-only, deferred |
| 5 | Merge/Admission Implementation | decision-only, deferred |
| 6 | Final Unlock/Creation Authorization Decision | nur falls explizit erlaubt |

## Spätere Implementierung — erst nach expliziter Öffnung

Diese Schritte bleiben offen und dürfen nicht durch die laufende Decision-only-Kette implizit entstehen:

1. Alembic-Datei erstellen:
   - `apps/api/alembic/versions/0008_module_projections.py`
   - `revision = "0008_module_projections"`
   - `down_revision = "0007_engine_result_storage"`
2. Tabelle `module_projections` definieren.
3. Indizes, Unique Constraints, Tenant Scope und Retention-Spalten definieren.
4. Rollback-Strategie definieren und testen.
5. ORM-Modell `ModuleProjection` ergänzen.
6. Projection Write Service ergänzen.
7. Worker Projection Materialization ergänzen.
8. Backfill-/Idempotenzkonzept ergänzen.
9. Neue Runtime Route nur mit OpenAPI + Route Security Manifest ergänzen.
10. Monitoring, Runbook und Cleanup-Policy ergänzen.

## Explizite Nicht-Ziele bis zur Öffnung

- Kein Vorab-Erstellen leerer Alembic-Dateien.
- Kein Shadow-Model `ModuleProjection`.
- Kein unregistrierter Service Stub für Projection Writes.
- Kein Worker-Codepfad, der materialisierte Projection schreibt.
- Kein Frontend- oder API-Pfad, der materialisierte Projection voraussetzt.

## Entscheidungslogik für spätere Öffnung

Ein späterer tatsächlicher Implementierungs-Gate muss mindestens bestätigen:

- Tenant-Isolation vollständig beschrieben.
- `module_results.result_payload_json` bleibt rekonstruierbare Wahrheit.
- Materialisierte Projection ist Cache/Read-Model, nicht Source of Truth.
- Backfill ist idempotent und unterbrechbar.
- Rollback löscht keine authoritative Result Payloads.
- Route Security Manifest und OpenAPI sind synchron.
- Keine raw/debug/internal Daten in Projection Storage.
