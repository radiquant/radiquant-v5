# 01 — Aktueller Status

## Letzter bestätigter Stand

| Bereich | Status |
|---|---|
| Letzter abgeschlossener Gate | `radi144_materialized_projection_migration_file_repository_file_admission_gate_decision` |
| Nächster Gate | `radi144_materialized_projection_migration_file_repository_file_admission_implementation_gate_decision` |
| Letzte Testbaseline | `221 passed` |
| Runtime Routes | `20` klassifiziert |
| Runtime OpenAPI Paths | `15` |
| LSP Diagnostics | `0` für neue/berührte Python-Dateien |
| Migration File | `apps/api/alembic/versions/0008_module_projections.py` absent |

## Harte Systeminvarianten

Diese Punkte sind weiterhin verbindlich:

- Kein Alembic-File `0008_module_projections.py` ohne späteren expliziten Gate.
- Keine Tabelle `module_projections`.
- Kein ORM-Modell `ModuleProjection`.
- Kein Projection Write Service.
- Keine Worker Projection Materialization.
- Keine neue Projection Runtime Route.
- `module_results.result_payload_json` bleibt Source of Truth.
- API Projection Reads bleiben on-demand aus `module_results.result_payload_json`.
- Safe Bundling nur innerhalb einer einzelnen Safety Boundary.
- Keine neue API-/Frontend-URL ohne OpenAPI + Route-Security Manifest.

## Aktuell erledigt

- Contract-/Schema-/Instance-Artefakte für alle bisherigen Radi144 Materialized Projection Decision-Gates sind vorhanden.
- Manifest-Anker in `packages/contracts/engines/radi144.engine-manifest.v1.json` sind bis Admission Decision fortgeschrieben.
- Projektanker in `docs/pi/project.yml` zeigt auf den nächsten Gate: Admission Implementation Decision.
- Validatoren und Tests sind in `scripts/verify_bootstrap.py`, `scripts/validate_contracts.py`, `scripts/check_radi144_engine_manifest.py` und `package.json` registriert.

## Aktuell offen

- Admission Implementation Decision Gate.
- Weitere Repository-File-Governance-Gates bis zu einer späteren expliziten Öffnung.
- Danach erst mögliche tatsächliche Migration-File-Erzeugung.
- Danach erst DB-/ORM-/Write-Service-/Worker-/Runtime-Implementierung, sofern separat freigegeben.
