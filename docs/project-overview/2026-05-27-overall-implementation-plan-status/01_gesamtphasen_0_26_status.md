# 01 — Gesamtphasen 0–26: Status und Einordnung

## Gesamtüberblick

| Nr. | Phase | Hauptziel | Aktueller Status | Fortschritt | Nächste Bedeutung |
|---:|---|---|---|---:|---|
| 0 | Entscheidungs-Freeze | Grundsatzentscheidungen bestätigen | erledigt | 100% | Scope-Drift vermeiden |
| 1 | Neuer Basisordner | sauberer v5-Projektraum | erledigt | 100% | `/opt/radiquant-v5` ist Arbeitsbasis |
| 2 | Tooling & Standards | Versionen, Verify, Grundstruktur | erledigt | 100% | `make verify` bleibt Gate |
| 3 | Contract Foundation | OpenAPI/Event/Workflow/Route-Manifeste | erledigt | 95% | keine URL/API/Event-Drift |
| 4 | Security Core | Auth, Rollen, Tenant, Audit | erledigt | 90% | keine unklassifizierte Route |
| 5 | Datenbank-Core | Basis-Migrationen und Tabellen | erledigt für Foundation, erweitert gegated | 75% | Projection-DB noch blockiert |
| 6 | Frontend-Shell | Login/Layout/Rollen/Design Tokens | erledigt | 85% | UI bleibt contract-bound |
| 7 | Klientenverwaltung | Client anlegen/anzeigen/bearbeiten | erledigt als Core | 80% | Vertiefung später möglich |
| 8 | Consent & Klientenakte | Consent, Notizen, Medienstrategie | teilweise erledigt | 55% | Consent Core vorhanden, Dokument-/Medienstrategie später |
| 9 | Session-Core | Session mit Ziel/Fokus/Typ | erledigt | 80% | Grundlage jeder Engine |
| 10 | Workflow Manifest v2 | Workflowtypen/Steps/Substeps/Phasen | erledigt | 95% | Modulsteuerung via Manifest |
| 11 | Realtime Foundation | EventBus/JobTracker/SSE/Replays | erledigt | 85% | Event-truth für UI |
| 12 | Erste vertikale Engine | Radi144 Musterpfad | in Arbeit / weit fortgeschritten | 70–75% | aktueller Schwerpunkt |
| 13 | Result Projections | Client/Therapist/Admin Trennung | teilweise erledigt | 45–55% | on-demand Projection vorhanden, Materialized Storage blockiert |
| 14 | Minimal Admin/Ops | Health/DB/Redis/Worker/Eventstatus | geplant | 10–20% | nach stabiler erster Engine sinnvoll |
| 15 | Engine Rollout 2–6 | übrige Kernengines integrieren | geplant | 0–10% | RadiWorks → RadiCopen nach Radi144-Muster |
| 16 | Synergy Merge | Cross-Module Synergie/Confidence/Konflikte | geplant | 0–5% | braucht mehrere Engine-Ergebnisse |
| 17 | Harmonization Plan | Analyse → Plan mit Approval | geplant | 0–5% | Safety/Approval vor Runtime |
| 18 | Harmonization Job | Timer/Pause/Resume/Stop/Hardware ACK | geplant | 0–5% | realtime- und safety-kritisch |
| 19 | Knowledge/Protocol Layer | Raten, Frequenzen, Protocol Library | geplant | 0–10% | versionierte Wiederverwendbarkeit |
| 20 | Reports & Exports | Client Report/Therapist Appendix | geplant | 0–5% | keine Raw-/Debugdaten im Client-Report |
| 21 | GDPR/Retention/Backup | Export/Löschung/Anonymisierung/Restore | geplant | 5–10% | rechtssichere Produktreife |
| 22 | UX/A11y Hardening | Chromotherapie/Circadian/Audio/A11y | geplant | 10–20% | nach funktionalem Kern konsolidieren |
| 23 | Full Verification Pipeline | Tests/Typecheck/OpenAPI/Route/Realtime CI | teilweise vorhanden, später vollständig | 45–55% | CI finalisieren |
| 24 | Deployment Baseline | Proxy/Ports/Secrets/systemd/Docker/Monitoring | geplant | 0–10% | reproduzierbares Staging/Local-Prod |
| 25 | Migration aus radiquant4 | selektive Algorithmen/Daten/Tests übernehmen | geplant | 0–10% | keine ungeprüfte Legacy-Übernahme |
| 26 | Innovation Labs | HRV/Quantum/LLM/SynergyGraph/Adaptive UX | geplant | 0–5% | nur feature-flagged, auditierbar, abschaltbar |

## Wichtigste Interpretation

Der Gesamtplan ist nicht linear im Sinne von „Phase 12 heißt 12/26 = 46%“. Die frühen Phasen enthalten die technische Basis, spätere Phasen enthalten viel Produktumfang. Deshalb ist die realistische Gesamtschätzung aktuell ca. **35–40%**.

## Phasencluster

| Cluster | Phasen | Status | Einschätzung |
|---|---|---|---:|
| Foundation/Core | 0–4 | weitgehend erledigt | 90–95% |
| Domain/Data/UI Basis | 5–11 | überwiegend erledigt, einzelne Vertiefungen offen | 75–85% |
| Radi144 Musterpfad + Projections | 12–13 | aktueller Schwerpunkt | 55–65% im Cluster |
| Produkt-/Ops-Ausbau | 14–24 | überwiegend geplant | 5–15% |
| Legacy-Migration + Innovation | 25–26 | geplant / später | 0–10% |

## Aktueller Arbeitsfokus

Aktuell arbeiten wir nicht „irgendwo im Gesamtplan“, sondern sehr gezielt an einem Subpfad:

`Phase 12 Radi144 Musterpfad` → `Phase 13 Result Projections` → `Radi144 materialized projection migration-file governance`

Dieser Subpfad schützt die spätere Einführung von `module_projections` vor Drift, Tenant-Fehlern und unkontrollierter Runtime-Öffnung.
