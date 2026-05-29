# 05 — Blocker, Stop-Regeln und nächste optimale Schritte

## 1. Harte Stop-Regeln

| Stop-Regel | Konsequenz |
|---|---|
| Frontend braucht URL ohne OpenAPI Contract | nicht implementieren, zuerst API Contract schaffen |
| API Route fehlt im Route Security Manifest | Gate/CI muss fehlschlagen |
| Engine liefert Daten ohne Result Schema | nicht ins UI integrieren |
| Workflow Step fehlt im Manifest | nicht anzeigen / nicht starten |
| Job sendet keine Events | keine Realtime-UI dafür bauen |
| Client sieht Raw-/Debugdaten | Release/Gate blockieren |
| Wrong-tenant Zugriff liefert Daten | Release/Gate blockieren |
| Audio/Report enthält Heil-/Diagnoseclaim | Release/Gate blockieren |
| `Radi144ResultWriter.persist_result` commitet intern | Gate blockieren |
| Materialized Projection schreibt ohne Write-Service-Gate | Gate blockieren |

## 2. Aktuell explizit blockierte technische Scopes

| Scope | Darf jetzt geöffnet werden? | Benötigter zukünftiger Gate |
|---|---:|---|
| GPU/CUDA Execution | nein | separater Execution/GPU Gate |
| API-triggered Execution über aktuelle Grenzen hinaus | nein | expliziter API Execution Gate |
| externe Queue/Daemon | nein | neuer External Queue/Daemon Gate |
| Worker Projection Materialization | nein | Worker Projection Materialization Implementation Gate |
| Materialized Projection Storage Writes | nein | Projection Write Service Gate |
| `module_projections` Table | nein | Table Creation Gate + ggf. Folgegate |
| `ModuleProjection` ORM Model | nein | ORM Model Implementation Gate |
| Alembic Projection Migration | nein | Migration/Table Creation Implementation Gate |
| Projection Write Service | nein | Write Service Gate |
| neue Projection Runtime Route | nein | OpenAPI + Route Security + Runtime Route Gate |
| Raw/Debug/Internal Projection Storage | nein | grundsätzlich blockiert, außer explizit sicherheitsgeprüfter Admin/Internal Gate |

## 3. Nächste optimale Schritte

| Reihenfolge | Schritt | Ziel | Wichtigste Grenze |
|---:|---|---|---|
| 1 | `radi144_materialized_projection_table_creation_gate_decision` | Entscheidung vorbereiten, ob/unter welchen Bedingungen eine Projection-Tabelle überhaupt geöffnet werden darf | erledigt: decision-only, keine Tabelle erzeugt |
| 2 | `radi144_materialized_projection_table_contract_gate_decision` | Table Contract/DDL Boundary weiter präzisieren: Spalten, Constraints, FKs, Indizes final gegen Security/Tenant/Retention prüfen | erledigt: keine Alembic Revision erzeugt |
| 3 | `radi144_materialized_projection_table_ddl_implementation_gate_decision` | entscheiden, ob/unter welchen Bedingungen DDL/Alembic geöffnet werden darf | erledigt: DDL bleibt deferred |
| 4 | `radi144_materialized_projection_alembic_revision_gate_decision` | Revision-ID, Upgrade/Downgrade-Plan und DB-Kompatibilität entscheiden | erledigt: Revision reserviert, keine Datei erzeugt |
| 5 | `radi144_materialized_projection_alembic_revision_implementation_gate_decision` | entscheiden, ob die Revision-Datei tatsächlich angelegt werden darf | erledigt: Datei bleibt deferred |
| 6 | `radi144_materialized_projection_migration_file_gate_decision` | entscheiden, ob die Datei `0008_module_projections.py` tatsächlich angelegt werden darf | erledigt: Datei bleibt deferred |
| 7 | `radi144_materialized_projection_migration_file_contract_gate_decision` | Upgrade-/Downgrade-Dateikontrakt vor Datei-Erzeugung präzisieren | erledigt: Datei bleibt deferred |
| 8 | `radi144_materialized_projection_migration_file_implementation_gate_decision` | entscheiden, ob die Datei-Erstellung später geöffnet werden darf | erledigt: Datei bleibt absent |
| 9 | `radi144_materialized_projection_migration_file_creation_gate_decision` | final entscheiden, ob die Alembic-Datei unter Contract angelegt werden darf | erledigt: Datei bleibt deferred |
| 10 | `radi144_materialized_projection_migration_file_content_contract_gate_decision` | exakten Dateiinhalt vor Datei-Erzeugung vertraglich festlegen | erledigt: Datei bleibt absent |
| 11 | `radi144_materialized_projection_migration_file_authoring_gate_decision` | entscheiden, ob die Datei gemäß Content Contract geschrieben werden darf | erledigt: Authoring bleibt deferred |
| 12 | `radi144_materialized_projection_migration_file_write_gate_decision` | entscheiden, ob die Datei tatsächlich geschrieben werden darf | erledigt: Write bleibt deferred |
| 13 | `radi144_materialized_projection_migration_file_write_implementation_gate_decision` | entscheiden, ob der Datei-Write implementiert werden darf | erledigt: Introduction bleibt deferred |
| 14 | `radi144_materialized_projection_migration_file_introduction_gate_decision` | entscheiden, ob die Datei ins Repo eingeführt werden darf | erledigt: Introduction bleibt deferred |
| 15 | `radi144_materialized_projection_migration_file_introduction_implementation_gate_decision` | entscheiden, ob die Repo-Einführung implementiert werden darf | erledigt: Repository-Introduction bleibt deferred |
| 16 | `radi144_materialized_projection_migration_file_repository_introduction_gate_decision` | entscheiden, ob die Datei wirklich ins Repo eingeführt werden darf | erledigt: Datei bleibt absent |
| 17 | `radi144_materialized_projection_migration_file_repository_introduction_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Einführung implementiert werden darf | erledigt: Datei bleibt absent |
| 18 | `radi144_materialized_projection_migration_file_repository_file_creation_gate_decision` | entscheiden, ob die Datei-Erzeugung im Repo wirklich geöffnet werden darf | erledigt: Datei bleibt absent |
| 19 | `radi144_materialized_projection_migration_file_repository_file_creation_implementation_gate_decision` | entscheiden, ob die Datei-Erzeugung implementiert werden darf | erledigt: Datei bleibt absent |
| 20 | `radi144_materialized_projection_migration_file_repository_file_write_gate_decision` | entscheiden, ob der Repository-Datei-Write geöffnet werden darf | erledigt: Datei bleibt absent |
| 21 | `radi144_materialized_projection_migration_file_repository_file_write_implementation_gate_decision` | entscheiden, ob der Repository-Datei-Write implementiert werden darf | erledigt: Datei bleibt absent |
| 22 | `radi144_materialized_projection_migration_file_repository_file_materialization_gate_decision` | entscheiden, ob die Repo-Datei materialisiert werden darf | erledigt: Datei bleibt absent |
| 23 | `radi144_materialized_projection_migration_file_repository_file_materialization_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Materialisierung implementiert werden darf | erledigt: Datei bleibt absent |
| 24 | `radi144_materialized_projection_migration_file_repository_file_execution_gate_decision` | entscheiden, ob die Repo-Datei tatsächlich ausgeführt/erstellt werden darf | erledigt: Datei bleibt absent |
| 25 | `radi144_materialized_projection_migration_file_repository_file_execution_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Ausführung implementiert werden darf | erledigt: Datei bleibt absent |
| 26 | `radi144_materialized_projection_migration_file_repository_file_enablement_gate_decision` | entscheiden, ob die Repo-Datei aktiviert werden darf | erledigt: Datei bleibt absent |
| 27 | `radi144_materialized_projection_migration_file_repository_file_enablement_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Aktivierung implementiert werden darf | erledigt: Datei bleibt absent |
| 28 | `radi144_materialized_projection_migration_file_repository_file_activation_gate_decision` | entscheiden, ob die Repo-Datei-Aktivierung geöffnet werden darf | erledigt: Datei bleibt absent |
| 29 | `radi144_materialized_projection_migration_file_repository_file_activation_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Aktivierung implementiert werden darf | erledigt: Datei bleibt absent |
| 30 | `radi144_materialized_projection_migration_file_repository_file_opening_gate_decision` | entscheiden, ob die Repo-Datei-Öffnung als expliziter Vor-Gate vorbereitet werden darf | erledigt: Datei bleibt absent |
| 31 | `radi144_materialized_projection_migration_file_repository_file_opening_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Öffnung implementiert werden darf | erledigt: Datei bleibt absent |
| 32 | `radi144_materialized_projection_migration_file_repository_file_release_gate_decision` | entscheiden, ob die Repo-Datei-Freigabe vorbereitet werden darf | erledigt: Datei bleibt absent |
| 33 | `radi144_materialized_projection_migration_file_repository_file_release_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Freigabe implementiert werden darf | erledigt: Datei bleibt absent |
| 34 | `radi144_materialized_projection_migration_file_repository_file_publication_gate_decision` | entscheiden, ob die Repo-Datei-Publikation vorbereitet werden darf | erledigt: Datei bleibt absent |
| 35 | `radi144_materialized_projection_migration_file_repository_file_publication_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Publikation implementiert werden darf | erledigt: Datei bleibt absent |
| 36 | `radi144_materialized_projection_migration_file_repository_file_finalization_gate_decision` | entscheiden, ob die Repo-Datei-Strecke finalisiert werden darf | erledigt: Datei bleibt absent |
| 37 | `radi144_materialized_projection_migration_file_repository_file_finalization_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Finalisierung implementiert werden darf | erledigt: Datei bleibt absent |
| 38 | `radi144_materialized_projection_migration_file_repository_file_closure_gate_decision` | entscheiden, ob die Repo-Datei-Strecke geschlossen/abgeschlossen werden darf | erledigt: Datei bleibt absent |
| 39 | `radi144_materialized_projection_migration_file_repository_file_closure_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Schließung implementiert werden darf | erledigt: Datei bleibt absent |
| 40 | `radi144_materialized_projection_migration_file_repository_file_readiness_gate_decision` | entscheiden, ob die Repo-Datei-Strecke bereit für spätere Öffnung ist | erledigt: Datei bleibt absent |
| 41 | `radi144_materialized_projection_migration_file_repository_file_readiness_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Bereitschaft implementiert werden darf | erledigt: Datei bleibt absent |
| 42 | `radi144_materialized_projection_migration_file_repository_file_preflight_gate_decision` | entscheiden, ob die Repo-Datei-Strecke in den Preflight darf | erledigt: Datei bleibt absent |
| 43 | `radi144_materialized_projection_migration_file_repository_file_preflight_implementation_gate_decision` | entscheiden, ob der Repo-Datei-Preflight implementiert werden darf | erledigt: Datei bleibt absent |
| 44 | `radi144_materialized_projection_migration_file_repository_file_validation_gate_decision` | entscheiden, ob die Repo-Datei-Validierung vorbereitet werden darf | erledigt: Datei bleibt absent |
| 45 | `radi144_materialized_projection_migration_file_repository_file_validation_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Validierung implementiert werden darf | erledigt: Datei bleibt absent |
| 46 | `radi144_materialized_projection_migration_file_repository_file_approval_gate_decision` | entscheiden, ob die Repo-Datei-Strecke zur späteren Genehmigung vorbereitet werden darf | erledigt: Datei bleibt absent |
| 47 | `radi144_materialized_projection_migration_file_repository_file_approval_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Genehmigung implementiert werden darf | erledigt: Datei bleibt absent |
| 48 | `radi144_materialized_projection_migration_file_repository_file_authorization_gate_decision` | entscheiden, ob die Repo-Datei-Autorisierung vorbereitet werden darf | erledigt: Datei bleibt absent |
| 49 | `radi144_materialized_projection_migration_file_repository_file_authorization_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Autorisierung implementiert werden darf | erledigt: Datei bleibt absent |
| 50 | `radi144_materialized_projection_migration_file_repository_file_permission_gate_decision` | entscheiden, ob die Repo-Datei-Berechtigung vorbereitet werden darf | erledigt: Datei bleibt absent |
| 51 | `radi144_materialized_projection_migration_file_repository_file_permission_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Berechtigungs-Implementierung vorbereitet werden darf | erledigt: Datei bleibt absent |
| 52 | `radi144_materialized_projection_migration_file_repository_file_access_gate_decision` | entscheiden, ob der Repo-Datei-Zugriff vorbereitet werden darf | erledigt: Datei bleibt absent |
| 53 | `radi144_materialized_projection_migration_file_repository_file_access_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Zugriffs-Implementierung vorbereitet werden darf | erledigt: Datei bleibt absent |
| 54 | `radi144_materialized_projection_migration_file_repository_file_review_gate_decision` | entscheiden, ob das Repo-Datei-Review vorbereitet werden darf | erledigt: Datei bleibt absent |
| 55 | `radi144_materialized_projection_migration_file_repository_file_review_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Review-Implementierung vorbereitet werden darf | erledigt: Datei bleibt absent |
| 56 | `radi144_materialized_projection_migration_file_repository_file_acceptance_gate_decision` | entscheiden, ob die Repo-Datei-Acceptance vorbereitet werden darf | erledigt: Datei bleibt absent |
| 57 | `radi144_materialized_projection_migration_file_repository_file_acceptance_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Acceptance-Implementierung vorbereitet werden darf | erledigt: Datei bleibt absent |
| 58 | `radi144_materialized_projection_migration_file_repository_file_admission_gate_decision` | entscheiden, ob die Repo-Datei-Admission vorbereitet werden darf | erledigt: Datei bleibt absent |
| 59 | `radi144_materialized_projection_migration_file_repository_file_admission_implementation_gate_decision` | entscheiden, ob die Repo-Datei-Admission-Implementierung vorbereitet werden darf | weiterhin keine Tabelle/kein ORM/kein Write Service |
| 60 | ggf. ORM Model Implementation Gate | `ModuleProjection` erst dann einführen, wenn Tabelle/Migration-Politik eindeutig ist | kein Write Service |
| 36 | ggf. Alembic Migration Gate | Revision kontrolliert erstellen/testen | keine Worker-Materialisierung |
| 37 | ggf. Projection Write Service Gate | persistierte Projection-Copy nur mit Hash/Role/Retention/Tenant Guards | kein API/Worker-Aufruf ohne Wiring Gate |
| 38 | ggf. Worker Materialization Gate | Worker darf Projection erst nach Write-Service und Event/Retry-Policy schreiben | kein externer Daemon ohne Gate |
| 39 | ggf. UI/Route Erweiterungen | neue Projection Views/Routes nur OpenAPI- und Route-Security-backed | keine Fake-URLs |

## 4. Empfohlene Arbeitsweise pro zukünftigem Gate

| Prüffrage | Erwartung |
|---|---|
| Gibt es einen klaren Contract? | Ja, vor Runtime-Code |
| Ist der Gate in `docs/pi/project.yml` verankert? | Ja |
| Ist die Radi144 Manifest-Grenze aktualisiert? | Ja, falls runtime-/contract-relevant |
| Gibt es Validator + Test? | Ja |
| Sind verbotene Tokens/Scopes weiter blockiert? | Ja |
| Läuft `make verify` vor und nach der Änderung? | Ja |
| Werden OpenAPI/Route Security verletzt? | Nein |
| Werden Tenant/Consent/Event-truth verletzt? | Nein |

## 5. Gute nächste Entscheidung für den Table Contract Gate

| Option | Stabilität | Empfehlung |
|---|---|---|
| Tabelle sofort implementieren | riskant | nicht empfohlen ohne weiteren Contract-/DDL-Split |
| Table Contract als Decision Gate dokumentieren | sehr stabil | empfohlen |
| DDL-Preconditions weiter präzisieren | stabil | empfohlen, falls im selben Safety Boundary |
| ORM/Migration/Write Service zusammen bündeln | riskant | nicht empfohlen |

## 6. Kurzempfehlung

Der nächste optimale Schritt sollte weiterhin klein bleiben:

`radi144_materialized_projection_migration_file_repository_file_admission_implementation_gate_decision`

Dabei sollte als nächstes nur entschieden werden, ob die Repo-Datei-Admission-Implementierung vorbereitet werden darf. ORM, Write-Service, Worker-Materialisierung und Runtime-Route bleiben weiterhin getrennt und blockiert.

Zusätzlich gilt künftig: sichere Arbeitserleichterungen dürfen gebündelt werden, aber nur innerhalb einer einzigen Safety Boundary und nie auf Kosten von Akkuranz oder Stabilität.
