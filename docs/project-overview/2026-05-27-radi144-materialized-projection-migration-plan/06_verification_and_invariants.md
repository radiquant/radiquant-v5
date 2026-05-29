# 06 — Verifikation und Invarianten

## Aktuelle Verifikationsmatrix

| Check | Erwartung | Letzter Status |
|---|---|---|
| `make verify` | exit 0 | grün |
| `python3 -m pytest tests --tb=short` | alle Tests grün | `221 passed` |
| `python3 scripts/check_runtime_routes.py` | klassifizierte Runtime Routes | `20` |
| `python3 scripts/check_openapi_runtime.py` | Runtime OpenAPI synchron | `15` Pfade |
| LSP Diagnostics | 0 Diagnostics für berührte Python-Dateien | grün |
| Absence Check | `0008_module_projections.py` existiert nicht | grün |

## Fail-Closed-Prüfungen

Die Gate-Validatoren prüfen weiterhin, dass folgende Tokens/Artefakte nicht unbemerkt eingeführt werden:

- `class ModuleProjection`
- `__tablename__ = "module_projections"`
- `op.create_table("module_projections"`
- `ProjectionWriteService`
- `persist_projection`
- geplante Alembic-Datei `apps/api/alembic/versions/0008_module_projections.py`

## Source-of-Truth-Invariante

`module_results.result_payload_json` bleibt authoritative Source of Truth. Materialisierte Projections dürfen später nur abgeleitete Read-Modelle/Caches sein.

## Tenant- und Compliance-Invarianten

- Jede spätere Projection muss tenant-scoped sein.
- Keine raw/debug/internal Felder in Projection Storage.
- Retention- und Provenance-Metadaten müssen erhalten bleiben.
- Rollback darf authoritative Result Payloads nicht löschen.
- Keine Wellbeing-/Compliance-Regression durch neue Projektionen.

## API-/Route-Invarianten

- Keine neue Runtime Route ohne OpenAPI-Contract.
- Keine neue Runtime Route ohne Route Security Manifest.
- Keine URL-Tokens.
- Keine Tenant-Isolation-Umgehung.

## Worker-/Execution-Invarianten

- Worker Projection Materialization bleibt blockiert.
- External Queue/Daemon bleibt für diesen Pfad blockiert.
- GPU/CUDA bleibt außerhalb dieses Migration-File-Pfads blockiert.
- API-triggered Execution bleibt durch bestehende Gates begrenzt.

## Minimal-invasive Arbeitsregel

Jeder nächste Gate-Schritt soll nur die kleinstmögliche, contract-first Änderung enthalten:

1. Schema/Instance für genau einen Gate.
2. Architektur-Dokument für genau diesen Gate.
3. Validator für genau diesen Gate.
4. Test, der den Validator ausführt.
5. Registrierung in Manifest, Bootstrap, Contract Validation und Projektanker.
6. Verifikation.
7. Keine Runtime-Öffnung ohne expliziten späteren Gate.
