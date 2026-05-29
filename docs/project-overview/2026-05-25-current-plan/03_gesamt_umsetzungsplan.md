# 03 — Gesamt-Umsetzungsplan

Grundlage: `/opt/radiquant4/docs/restart-radiquant-v5/08_OPTIMAL_REBUILD_SEQUENCE.md` und der aktuelle v5-Stand in `docs/pi/project.yml`.

## 1. Gesamtphasen 0–26

| Nr. | Phase | Hauptziel | Aktueller Status | Nächste Bedeutung |
|---:|---|---|---|---|
| 0 | Entscheidungs-Freeze | Grundsatzentscheidungen bestätigen | erledigt | Scope-Drift vermeiden |
| 1 | Neuer Basisordner | sauberer v5-Projektraum | erledigt | `/opt/radiquant-v5` ist Arbeitsbasis |
| 2 | Tooling & Standards | Versionen, Verify, Grundstruktur | erledigt | `make verify` bleibt Gate |
| 3 | Contract Foundation | OpenAPI/Event/Workflow/Route-Manifeste | erledigt | keine URL/API/Event-Drift |
| 4 | Security Core | Auth, Rollen, Tenant, Audit | erledigt | keine unklassifizierte Route |
| 5 | Datenbank-Core | Basis-Migrationen und Tabellen | erledigt für Foundation, erweitert gegated | Projection-DB noch blockiert |
| 6 | Frontend-Shell | Login/Layout/Rollen/Design Tokens | erledigt | UI bleibt contract-bound |
| 7 | Klientenverwaltung | Client anlegen/anzeigen/bearbeiten | erledigt als Core | Vertiefung später möglich |
| 8 | Consent & Klientenakte | Consent, Notizen, Medienstrategie | teilweise erledigt | Consent Core vorhanden, Dokument-/Medienstrategie später |
| 9 | Session-Core | Session mit Ziel/Fokus/Typ | erledigt | Grundlage jeder Engine |
| 10 | Workflow Manifest v2 | Workflowtypen/Steps/Substeps/Phasen | erledigt | Modulsteuerung via Manifest |
| 11 | Realtime Foundation | EventBus/JobTracker/SSE/Replays | erledigt | Event-truth für UI |
| 12 | Erste vertikale Engine | Radi144 Musterpfad | in Arbeit / weit fortgeschritten | aktueller Schwerpunkt |
| 13 | Result Projections | Client/Therapist/Admin Trennung | teilweise erledigt | on-demand Projection offen, Materialized Storage blockiert |
| 14 | Minimal Admin/Ops | Health/DB/Redis/Worker/Eventstatus | geplant | nach stabiler erster Engine sinnvoll |
| 15 | Engine Rollout 2–6 | übrige Kernengines integrieren | geplant | RadiWorks → RadiCopen nach Radi144-Muster |
| 16 | Synergy Merge | Cross-Module Synergie/Confidence/Konflikte | geplant | braucht mehrere Engine-Ergebnisse |
| 17 | Harmonization Plan | Analyse → Plan mit Approval | geplant | Safety/Approval vor Runtime |
| 18 | Harmonization Job | Timer/Pause/Resume/Stop/Hardware ACK | geplant | realtime- und safety-kritisch |
| 19 | Knowledge/Protocol Layer | Raten, Frequenzen, Protocol Library | geplant | versionierte Wiederverwendbarkeit |
| 20 | Reports & Exports | Client Report/Therapist Appendix | geplant | keine Raw-/Debugdaten im Client-Report |
| 21 | GDPR/Retention/Backup | Export/Löschung/Anonymisierung/Restore | geplant | rechtssichere Produktreife |
| 22 | UX/A11y Hardening | Chromotherapie/Circadian/Audio/A11y | geplant | nach funktionalem Kern konsolidieren |
| 23 | Full Verification Pipeline | Tests/Typecheck/OpenAPI/Route/Realtime CI | teilweise vorhanden, später vollständig | CI finalisieren |
| 24 | Deployment Baseline | Proxy/Ports/Secrets/systemd/Docker/Monitoring | geplant | reproduzierbares Staging/Local-Prod |
| 25 | Migration aus radiquant4 | selektive Algorithmen/Daten/Tests übernehmen | geplant | keine ungeprüfte Legacy-Übernahme |
| 26 | Innovation Labs | HRV/Quantum/LLM/SynergyGraph/Adaptive UX | geplant | nur feature-flagged, auditierbar, abschaltbar |

## 2. Detaillierte Schritte 1–48 mit aktuellem Status

| Nr. | Schritt | Aktueller Status | Hinweis |
|---:|---|---|---|
| 1 | Offene Entscheidungen bestätigen | erledigt | Decision Freeze / Scope-Grundlage vorhanden |
| 2 | v5-Projektordner anlegen | erledigt | `/opt/radiquant-v5` |
| 3 | Basisdokumente übernehmen | erledigt | Architecture-/Contract-Dokumente vorhanden |
| 4 | Toolchain pinnen | erledigt | Python/Node/Verify vorhanden |
| 5 | CI-Grundlage erstellen | teilweise erledigt | lokale Verify-Pipeline stabil, CI-Ausbau später |
| 6 | API-Skeleton | erledigt | Health/App/Config-Basis vorhanden |
| 7 | Frontend-Skeleton | erledigt | Shell ohne Fake-URLs |
| 8 | DB-Migration-Skeleton | erledigt | Alembic-Basis vorhanden |
| 9 | Identity Core | erledigt | Auth/User/Tenant/Rollen |
| 10 | Route Security Manifest | erledigt | unklassifizierte Route failt |
| 11 | Tenant Guards | erledigt | wrong-tenant Schutz als Prinzip |
| 12 | Audit Core | erledigt | Audit-Basis vorhanden |
| 13 | Client Domain API | erledigt | Client API vorhanden |
| 14 | Client Frontend | erledigt | Client UI Core vorhanden |
| 15 | Consent Domain | erledigt | Consent Gate vorhanden |
| 16 | Session Domain | erledigt | Session Core vorhanden |
| 17 | Workflow Manifest v2 | erledigt | Manifest validiert |
| 18 | Workflow API | erledigt | Workflow API Gate vorhanden |
| 19 | Event Schema | erledigt | Event Schema Gate vorhanden |
| 20 | Realtime API | erledigt | SSE/Event Replay vorhanden |
| 21 | JobTracker UI | erledigt | Event-bound JobTracker Basis |
| 22 | Erste Engine auswählen | erledigt | Radi144 ist erste vertikale Engine |
| 23 | Engine Manifest | erledigt | Radi144 Manifest validiert |
| 24 | Engine Domain Service | erledigt | Radi144 Domain/CPU-safe Logik vorhanden |
| 25 | Engine Job | teilweise erledigt | Job Records/Worker Runtime vorhanden, externe Queue blockiert |
| 26 | Engine API | teilweise erledigt | Radi144 Runtime Routes vorhanden, API-triggering bleibt gegated |
| 27 | Engine UI | teilweise erledigt | JobTracker/Event Binding vorhanden; tiefere Therapist/Client Views später |
| 28 | Engine Result Storage | erledigt für ModuleResult | Materialized Projection Storage noch blockiert |
| 29 | Erste vertikale Demo | teilweise erledigt | Backend/Event/Projection-Pfad weit; vollständige UI-E2E später |
| 30 | Minimal Admin/Ops | geplant | nach stabiler Radi144-Strecke |
| 31 | RadiWorks integrieren | geplant | zweite Engine nach Radi144-Muster |
| 32 | RadiMorphic integrieren | geplant | Analyse-Engine nach Pattern |
| 33 | RadiBlohm integrieren | geplant | Morphic Field / Plan-Kandidaten |
| 34 | RadiThoms integrieren | geplant | Harmonize/5D/Meridian/Hardware-Fallback |
| 35 | RadiCopen integrieren | geplant | Copen/Level Resonance/safe Interpretation |
| 36 | Cross-Module Synergy | geplant | erst nach mehreren Engine-Ergebnissen |
| 37 | Protocol Library | geplant | versionierte Analyse-/Harmonize-Protokolle |
| 38 | Knowledge DB | geplant | Rates/Frequencies/Patterns/Source Versioning |
| 39 | Harmonization Plan | geplant | Therapist Approval Gate |
| 40 | Harmonization Runtime | geplant | Timer/Pause/Resume/Stop/ACK |
| 41 | Reports | geplant | Client Report + Therapist Appendix |
| 42 | GDPR Tools | geplant | Export/Delete/Anonymize/Retention |
| 43 | Backup/Restore | geplant | Restore-Test und Runbook |
| 44 | UX-Härtung | geplant | Chromotherapie/Circadian/Audio/A11y |
| 45 | Security Hardening | geplant | Secret Scan, Dependency Audit, CORS/CSP, MFA |
| 46 | Deployment | geplant | Reverse Proxy, Services, Monitoring |
| 47 | Migration radiquant4 | geplant | nur selektiv und geprüft |
| 48 | Labs freischalten | geplant | HRV/Quantum/LLM nur feature-flagged |

## 3. Aktueller Schwerpunkt innerhalb des Gesamtplans

| Planabschnitt | Aktueller Zustand |
|---|---|
| Phase 12 — Erste vertikale Engine | Radi144 ist in der kontrollierten Backend-/Event-/Projection-Strecke weit fortgeschritten |
| Phase 13 — Result Projections | on-demand Projection aktiv, Materialized Projection bleibt bewusst deferred |
| Nächster konkreter Mini-Gate | `radi144_materialized_projection_migration_file_repository_file_admission_implementation_gate_decision` |
| Wichtigste Regel | Kein DB-/ORM-/Migration-/Write-Service-Sprung ohne expliziten Gate |
