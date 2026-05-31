# 06 — Vollständiger Entwicklungsplan W3–W9 (+ G-01 Governance-Schuld)

> **Stand:** 2026-05-30 · Erstellt von Cascade nach vollständiger Codebase-Tiefenanalyse.
> **Zweck:** Maximale Präzision, vollständige Detaillierung, optimale Ausführungsreihenfolge.
> **Methode:** Jedes Ticket ist sofort ausführbar — mit Agent, Scope, konkreter Änderungsbeschreibung, Akzeptanzkriterien und Verifikationsbefehl.
> **Legende:** Codex = Codex CLI | Cascade = Cascade direkt | Devin = autonom + PR | Gemini = Gemini 3.1 Pro (1M Kontext)

---

## Gesamtreihenfolge (optimale Sequenz mit Abhängigkeiten)

```
G-01  →  W3a → W3b → W3c → W3d
      →  W4a → W4b → W4c → W4d
      →  W5a → W5b → W5c
      →  W6-ADR → W6a → W6b → W6c → W6d → W6e
      →  W7a → W7b → W7c → W7d
      →  W8a → W8b → W8c → W8d
      →  W9a → W9b → W9c → W9d
```

**Kritische Pfadabhängigkeiten:**

| Blockierung | Grund |
|---|---|
| **G-01 vor W3c** | `validate_contracts.py` Radi144-Kaskade kollidiert mit Worker-Events und neuen Service-Zuständen |
| **W4b vor W4c** | Playwright-E2E braucht existierende MVP-Seiten |
| **W6 komplett vor W7** | SynergyService braucht alle 6 Engine-Ergebnisse |
| **W7 komplett vor W8** | Reports/Harmonisierung erst mit vollständigem Datensatz |
| **W8 vor W9** | Deployment-Baseline Voraussetzung für Labs |

---

## G-01 — Governance-Schuld: validate_contracts.py Radi144-Kaskade

| Feld | Wert |
|---|---|
| **Agent** | Gemini 3.1 Pro (1M Kontext) ODER Cascade direkt |
| **Vorbedingung** | W2 abgeschlossen (✅) |
| **Risiko** | HOCH — Kaskade erzwingt "disabled/absent" für Features die in W2 implementiert wurden; kollidiert in W3c |
| **Dateien** | `scripts/validate_contracts.py` (~Z. 2000–2142), `docs/pi/project.yml` |

**Was zu tun ist:**

`scripts/validate_contracts.py` enthält eine große Radi144-Decision-Kaskade (ca. Z. 2000–2142) die unter ADR-0001 eingefroren wurde, aber nie explizit unter ADR-0002 entschieden wurde. Sie erzwingt:
- `result_persistence_enabled: disabled`
- `projection_builder_enabled: disabled`
- `projection_materialization_enabled: disabled`
- `gpu_execution_enabled: disabled`

W2 hat die ersten drei aktiviert (ADR-0002). GPU bleibt frozen. Die Kaskade ist damit **teilweise obsolet**.

**Gemini-Prompt (copy-paste-fertig für Gemini 3.1 Pro):**

```
Du arbeitest im Projekt /opt/radiquant-v5. Lies vollständig:
1. /opt/radiquant-v5/scripts/validate_contracts.py (komplett, alle Zeilen)
2. /opt/radiquant-v5/docs/architecture/adr/ADR-0001-decision-gate-cascade-frozen.md
3. /opt/radiquant-v5/docs/architecture/adr/ADR-0002-radi144-materialized-projection-storage.md
4. /opt/radiquant-v5/docs/pi/project.yml (komplett)

Aufgabe: Identifiziere und bereinige die Radi144-Decision-Kaskade (~Z. 2000–2142 in validate_contracts.py)
unter ADR-0002-Governance.

Regeln:
- gpu_execution_enabled: disabled → bleibt (ADR-0001 gilt weiter für GPU)
- result_persistence_enabled: enabled → Kaskade-Check muss entfernt/angepasst werden (W2a implementiert)
- projection_builder_enabled: enabled → wie oben (W2b)
- projection_materialization_enabled: enabled → wie oben (W2b/W2c)
- Alle anderen Frozen-Era-Anchors BLEIBEN erhalten

Scope: Nur validate_contracts.py und project.yml anpassen. Kein git commit.
Verifikation: pytest tests/ -q (erwartet: alle grün)
```

**Akzeptanzkriterien:**
- `pytest tests/ -q` → alle Tests grün
- `python3 scripts/validate_contracts.py` → exit 0
- GPU-Anchors (`gpu_execution_enabled: disabled`) bleiben erhalten

---

## W3 — Realtime & Result-Projektionen

### W3a — SSE-Protokoll: Last-Event-ID + retry + replay.complete

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Vorbedingung** | keine (unabhängig) |
| **Dateien** | `apps/api/app/routes/realtime.py` |

**Genaue Änderungen:**

1. `stream_session_events` Handler: `Request`-Parameter ergänzen; `Last-Event-ID` Header (case-insensitive) als Alternative zu `after_event_id` Query-Param lesen — Header hat Vorrang, da Browser ihn bei Reconnect automatisch sendet.
2. `event_stream()` Generator: vor allen Events einmalig `retry: 3000\n\n` emittieren.
3. `event_stream()` Generator: nach dem letzten Event `event: replay.complete\ndata: {}\n\n` emittieren.
4. Import `Request` aus fastapi ergänzen.

**Codex-Prompt:**

```
Du arbeitest im Projekt /opt/radiquant-v5. Lies zuerst AGENTS.md.

Aufgabe: W3a — SSE-Protokoll-Verbesserungen in apps/api/app/routes/realtime.py.

LIES ZUERST: apps/api/app/routes/realtime.py

SCOPE: Nur apps/api/app/routes/realtime.py ändern. Kein git commit.

AUFGABE:
1. stream_session_events-Handler: Request-Parameter hinzufügen (from fastapi import Request).
   Last-Event-ID Header (request.headers.get("last-event-id") oder "Last-Event-ID")
   als Alternative zu after_event_id Query-Param lesen.
   Wenn Header gesetzt → UUID daraus parsen und als after_event_id nutzen (Header schlägt Query-Param).

2. In event_stream() AsyncIterator:
   - Als allererste Zeile: yield "retry: 3000\n\n"
   - Nach allen Item-Events als letzte Zeile: yield "event: replay.complete\ndata: {}\n\n"

SELBSTPRÜFUNG:
  pytest tests/test_realtime_routes.py -v
  (bestehende 5 Tests müssen weiter grün bleiben)

MELDE ZURÜCK: pytest-Output. Kein git commit.
```

**Akzeptanzkriterien:**
- `retry: 3000` am Anfang jedes SSE-Streams
- Browser-`Last-Event-ID`-Header wird korrekt als Cursor ausgewertet
- `event: replay.complete` am Ende des Streams
- Alle 5 bestehenden Realtime-Tests grün

---

### W3b — Polling-Response: has_more

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Vorbedingung** | W3a ✅ |
| **Dateien** | `apps/api/app/schemas/realtime.py`, `apps/api/app/routes/realtime.py` |

**Genaue Änderungen:**

1. `EventReplayResponse` bekommt `has_more: bool = False`.
2. `_load_events`: Query nutzt `limit + 1`; wenn `len(records) > limit` → `has_more=True`, `records = records[:limit]`.
3. `_load_events` Rückgabe-Typ erweitern: `tuple[list[EventReplayItem], UUID | None, bool]`.
4. Beide Route-Handler geben `has_more` an `EventReplayResponse` weiter.

**Codex-Prompt:**

```
Du arbeitest im Projekt /opt/radiquant-v5. Lies zuerst AGENTS.md.

Aufgabe: W3b — has_more-Feld in EventReplayResponse.

LIES ZUERST:
  apps/api/app/schemas/realtime.py
  apps/api/app/routes/realtime.py

SCOPE: Nur diese zwei Dateien. Kein git commit.

AUFGABE:
1. schemas/realtime.py: EventReplayResponse bekommt has_more: bool = False

2. routes/realtime.py:
   - _event_statement: limit-Parameter intern zu limit+1 fetchen (LIMIT+1-Trick)
   - _load_events: prüft ob len(records) > limit → has_more=True, records=records[:limit]
   - Rückgabe-Tupel wird zu (items, next_cursor, has_more)
   - Beide Route-Handler übergeben has_more an EventReplayResponse

SELBSTPRÜFUNG:
  pytest tests/test_realtime_routes.py -v

MELDE ZURÜCK: pytest-Output. Kein git commit.
```

**Akzeptanzkriterien:**
- `has_more=True` wenn exakt `limit` Items im Response (more data available)
- `has_more=False` wenn weniger als `limit` Items
- Bestehende Tests grün

---

### W3c — Rollen-Projektion für Event-Payloads

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Vorbedingung** | G-01 ✅, W3b ✅ |
| **Dateien** | `apps/api/app/services/event_registry.py`, `apps/api/app/schemas/realtime.py`, `apps/api/app/routes/realtime.py` |

**Genaue Änderungen:**

1. `event_registry.py`: Neue Konstante `CLIENT_HIDDEN_PAYLOAD_KEYS = {"compute_backend", "module_run_id", "gpu_cuda_execution_enabled", "cpu_execution_enabled", "worker_outcome", "projection_written"}`. Neue Funktion `project_payload_for_role(payload, role)`: für `role="client"` alle `CLIENT_HIDDEN_PAYLOAD_KEYS` aus payload entfernen (rekursiv); für `therapist`/`admin` unverändert zurückgeben.
2. `schemas/realtime.py`: `EventReplayRole = Literal["client", "therapist", "admin"]` Typ-Alias.
3. `routes/realtime.py`: `role: Annotated[EventReplayRole, Query(...)] = "therapist"` Parameter in beide Endpunkte. `_project_event` bekommt `role`-Parameter und ruft `project_payload_for_role` auf.

**Codex-Prompt:**

```
Du arbeitest im Projekt /opt/radiquant-v5. Lies zuerst AGENTS.md.

Aufgabe: W3c — Rollen-Projektion für Event-Payloads.

LIES ZUERST:
  apps/api/app/services/event_registry.py
  apps/api/app/schemas/realtime.py
  apps/api/app/routes/realtime.py

SCOPE: Diese drei Dateien. Kein git commit.

AUFGABE:

1. services/event_registry.py:
   Neue Modul-level Konstante:
     CLIENT_HIDDEN_PAYLOAD_KEYS = {
         "compute_backend", "module_run_id", "gpu_cuda_execution_enabled",
         "cpu_execution_enabled", "worker_outcome", "projection_written",
     }
   Neue Top-Level-Funktion:
     def project_payload_for_role(payload: dict[str, Any], role: str) -> dict[str, Any]:
         if role == "client":
             return {k: v for k, v in payload.items() if k not in CLIENT_HIDDEN_PAYLOAD_KEYS}
         return payload

2. schemas/realtime.py:
   Typ-Alias ergänzen: EventReplayRole = Literal["client", "therapist", "admin"]

3. routes/realtime.py:
   - EventReplayRole importieren (aus app.schemas.realtime)
   - project_payload_for_role importieren (aus app.services.event_registry)
   - Beide Endpunkte (list + stream) bekommen:
       role: Annotated[EventReplayRole, Query()] = "therapist"
   - _project_event bekommt role-Parameter und ruft project_payload_for_role(record.payload_json, role) auf
   - _load_events bekommt role-Parameter, gibt ihn an _project_event weiter
   - Alle Aufrufer aktualisieren

SELBSTPRÜFUNG:
  pytest tests/test_realtime_routes.py -v

MELDE ZURÜCK: pytest-Output. Kein git commit.
```

**Akzeptanzkriterien:**
- `?role=client` → `compute_backend`, `module_run_id`, `worker_outcome` fehlen im Payload
- `?role=therapist` → vollständiges Payload
- `?role=admin` → vollständiges Payload
- Default ist `therapist`
- Alle bestehenden Tests grün

---

### W3d — Erweiterter Test-Suite für W3a–W3c

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Vorbedingung** | W3a ✅, W3b ✅, W3c ✅ |
| **Dateien** | `tests/test_realtime_routes.py` |

**Neue Tests (je einer pro neues Verhalten):**
1. `test_stream_contains_retry_directive` — `retry: 3000` im SSE-Stream
2. `test_stream_ends_with_replay_complete` — `event: replay.complete` als letztes Event
3. `test_stream_respects_last_event_id_header` — `Last-Event-ID: <uuid>` → nur Events danach
4. `test_polling_has_more_true_when_page_full` — `limit=1`, 2 Events → `has_more=True`
5. `test_polling_has_more_false_when_page_partial` — `limit=10`, 2 Events → `has_more=False`
6. `test_client_role_hides_forbidden_payload_keys` — Worker-Event mit `compute_backend` → `?role=client` gibt es nicht zurück
7. `test_therapist_role_sees_all_payload_keys` — gleiches Event → `?role=therapist` gibt alles zurück

**Verifikation:** `pytest tests/ -q` → alle Tests grün (mind. 7 neue)

---

## W4 — Frontend-Test-Harness + MVP-Demo

### W4a — Vitest-Setup + Island-Unit-Tests

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Vorbedingung** | keine (parallel zu W3 möglich) |
| **Dateien** | `apps/web-astro/package.json`, `apps/web-astro/vitest.config.ts` (neu), `apps/web-astro/src/components/__tests__/` (neu) |

**Genaue Änderungen:**

1. `package.json`: `vitest`, `@vitejs/plugin-react`, `@testing-library/react`, `@testing-library/user-event`, `jsdom` als devDependencies ergänzen. Script `"test": "vitest run"` ergänzen.
2. `vitest.config.ts` anlegen: jsdom environment, React plugin.
3. Vier Unit-Tests anlegen:
   - `LoginShell.test.tsx` — renders login form, submit calls onSubmit
   - `ClientListIsland.test.tsx` — empty state renders "Keine Klienten"
   - `ConsentIsland.test.tsx` — renders consent checkbox, onChange
   - `JobTrackerStatusIsland.test.tsx` — renders connection state labels, load button disabled without input

**Akzeptanzkriterien:** `npm run test` in `apps/web-astro` → min. 4 passed, 0 failed

---

### W4b — MVP-Seiten: Workflow + Radi144-Result-View

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Vorbedingung** | W2 ✅ |
| **Dateien** | `apps/web-astro/src/pages/sessions/[session_id]/workflow.astro` (neu), `apps/web-astro/src/pages/sessions/[session_id]/radi144/[job_id].astro` (neu), `apps/web-astro/src/lib/api/client.ts` (ergänzen) |

**Genaue Änderungen:**

1. `workflow.astro`: SSR-Seite die WorkflowRuns für die Session listet (`GET /sessions/{id}/workflow-runs`) + Formular für neuen WorkflowRun (`POST /sessions/{id}/workflow-runs`, workflow_id="W-A"). Authentifizierung über Cookie (wie bestehende Seiten). Fehlerstate zeigen.
2. `radi144/[job_id].astro`: SSR-Seite die Radi144-Job-Status zeigt (`GET /engines/radi144/jobs/{id}`). Wenn Status `completed` → Projektion laden (`GET /engines/radi144/jobs/{id}/result?role=therapist`) und darstellen. Keine Rohdaten. JobTrackerStatusIsland einbinden.
3. `lib/api/client.ts`: `getWorkflowRuns(sessionId)`, `createWorkflowRun(sessionId, workflowId)`, `getRadi144Result(jobId, role)` Funktionen ergänzen.

**Akzeptanzkriterien:**
- `/sessions/{id}/workflow` rendert ohne 500
- `/sessions/{id}/radi144/{job_id}` rendert Projektion wenn Job abgeschlossen
- Kein Raw-Debug in der Ausgabe

---

### W4c — Playwright E2E: Login→Client→Session→Result

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI + Devin (optional für Breite) |
| **Vorbedingung** | W4a ✅, W4b ✅ |
| **Dateien** | `apps/web-astro/playwright.config.ts` (neu), `apps/web-astro/tests/e2e/` (neu) |

**Flows:**

1. `auth.spec.ts`: Login mit gültigen Credentials → Dashboard sichtbar. Login mit falschem Passwort → Fehlermeldung.
2. `client.spec.ts`: Client anlegen → in Liste erscheinen. Client-Detail aufrufen.
3. `consent.spec.ts`: Zustimmung erteilen → Consent-Status ändert sich.
4. `session.spec.ts`: Session anlegen → Workflow-Run anlegen → Job anlegen.
5. `radi144_result.spec.ts`: Job-Status-Seite aufrufen → Projektion sichtbar wenn completed.

**Verifikation:** `npx playwright test` in `apps/web-astro` → alle Flows grün

---

### W4d — A11y-Smoke (WCAG AA)

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Vorbedingung** | W4c ✅ |
| **Dateien** | `apps/web-astro/tests/e2e/a11y.spec.ts` (neu) |

**axe-playwright** Integration: jede Hauptseite (login, dashboard, clients, radi144-result) mit `checkA11y()` prüfen. WCAG AA Level. Kontrast, ARIA-Labels, Keyboard-Navigation.

**Akzeptanzkriterien:** 0 axe-violations mit Level AA auf allen MVP-Seiten

---

## W5 — Minimal Admin/Ops

### W5a — Erweiterter Health-Endpunkt

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Vorbedingung** | keine |
| **Dateien** | `apps/api/app/routes/health.py`, `apps/api/app/schemas/health.py` |

**Genaue Änderungen:**

Aktuell gibt `GET /health` nur `{"status": "ok"}` zurück. Erweiterung auf:

```json
{
  "status": "ok|degraded|unhealthy",
  "db": "ok|error",
  "migration_head": "0008",
  "checks": {"db_ping": true, "tables_present": true},
  "version": "0.0.0"
}
```

1. `HealthDetailResponse` Schema anlegen.
2. Route führt `SELECT 1` gegen DB aus; bei Fehler → `status="unhealthy"`, HTTP 503.
3. Prüft ob `module_projections` in den Tabellennamen vorkommt (stichprobenartig).
4. Gibt Migration-Head aus `alembic_version` Tabelle zurück.

**Akzeptanzkriterien:**
- `GET /health` → 200 mit vollständigem JSON wenn DB erreichbar
- `GET /health` → 503 wenn DB nicht erreichbar
- Tests in `tests/test_health_route.py` (neu)

---

### W5b — Admin-Routen: Audit-Log + Stats

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Vorbedingung** | W5a ✅ |
| **Dateien** | `apps/api/app/routes/admin.py` (neu), `apps/api/app/main.py`, `apps/api/app/schemas/admin.py` (neu) |

**Endpunkte:**

1. `GET /admin/audit-log?limit=50&offset=0` — Paginiertes Audit-Log (admin-only, gleicher TenantContext wie andere Routen). Felder: `id`, `actor_user_id`, `action`, `resource_type`, `resource_id`, `reason`, `occurred_at`.
2. `GET /admin/stats` — Zähler: Sessions (total/active), WorkflowRuns (total/planned), ModuleRuns (total/queued/completed/failed), EventRecords (total). Alles tenant-scoped.
3. `GET /admin/routes` — Statische Liste aller registrierten Route-Pfade + Operation-IDs aus dem Router.

**Vorbedingung für Zugriff:** `require_tenant_context` (bestehender Guard). Rollenprüfung auf `RoleName.THERAPIST` oder höher (bis Admin-Rolle in W6+ definiert wird).

**Akzeptanzkriterien:**
- Alle 3 Endpunkte antworten korrekt
- Tests `tests/test_admin_routes.py` (neu) → min. 6 passed

---

### W5c — Ops-Baseline: Docker + systemd + Prometheus

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Vorbedingung** | W5b ✅ |
| **Dateien** | `infra/docker/docker-compose.yml` (neu), `infra/docker/nginx.conf` (neu), `infra/systemd/radiquant-api.service` (neu), `apps/api/app/routes/metrics.py` (neu) |

**Genaue Änderungen:**

1. `docker-compose.yml`: Services `api` (FastAPI via uvicorn), `db` (postgres:16), `nginx` (reverse proxy → api:8000). Healthchecks. Volume für DB-Daten.
2. `nginx.conf`: Reverse proxy auf `api:8000`, X-Forwarded-For, Gzip.
3. `radiquant-api.service`: systemd-Unit für direkten Produktionseinsatz ohne Docker.
4. `metrics.py`: `GET /metrics` mit prometheus-client (Counter für HTTP-Requests nach Status + Methode, aktive Verbindungen). Nur lesbar ohne Auth.
5. `prometheus.yml` in `infra/monitoring/` — Scrape-Config für den API-Endpunkt.

**Akzeptanzkriterien:**
- `docker-compose up -d` bringt API + DB hoch
- `GET /metrics` → Prometheus-Format (text/plain)
- systemd-Unit syntaktisch valide (`systemd-analyze verify`)

---

## W6 — Engine-Rollout 2–6 (Devin-primär)

### W6-ADR — Scaffold-Contract pro Engine (Cascade erstellt)

Vor Devin-Start: Cascade erstellt `ADR-0003-engine-rollout-scaffold.md` mit:
- Kanonisches Datei-Layout pro Engine (Migration, ORM, Service, Worker, Route, Schema, Test)
- Verbindlicher Code-Stil (exakt wie Radi144-Muster)
- Algorithmus-Port-Richtlinien (selektiv aus radiquant4, kein Copy-Dump)
- Rollback-Strategie pro Engine-Branch

### W6a — RadiWorks Engine (Raten-Analyse, Monte-Carlo-Scoring)

| Feld | Wert |
|---|---|
| **Agent** | Devin (Feature-Branch `feature/w6a-radiworks`) |
| **Vorbedingung** | W6-ADR ✅, W2 ✅ |
| **Algorithmus-Quelle** | `/opt/radiquant4/apps/engines/radiworks/` |

**Scope (Devin-Ticket):**
1. Migration `0009_radiworks_results.py` — Tabelle `radiworks_results` mit `module_run_id FK`, `tenant_id`, `result_payload_json`, `projection_status`.
2. ORM `apps/api/app/models/radiworks.py` — `RadiWorksResult`.
3. Service `apps/api/app/services/radiworks/` — Port von `radiquant4`: `analyse_rate_list()`, `general_vitality_check()`, `monte_carlo_scoring()`. Kein GPU-Pfad. Idempotenter Result-Writer. Projection-Writer (Client/Therapist).
4. Worker `apps/api/app/services/radiworks/worker_runtime.py` — exakt nach Radi144-Muster.
5. Routes `apps/api/app/routes/radiworks.py` — `POST /engines/radiworks/jobs`, `GET /engines/radiworks/jobs/{id}`, `GET /engines/radiworks/jobs/{id}/result?role=`.
6. Tests `tests/test_radiworks_*.py` — Domain, Worker, API (mind. 15 Tests).
7. Frontend `apps/web-astro/src/pages/sessions/[session_id]/radiworks/[job_id].astro`.

**Akzeptanzkriterien:** CI grün, PR reviewt von Cascade, Tenant-Isolation getestet.

---

### W6b — RadiMorphic Engine (Hadamard S-Matrix, NLS-Profil-Resonanz)

Identisches Schema wie W6a. Algorithmus-Quelle: `radiquant4/apps/engines/radimorphic/`. Besonderheit: `multiplex_scan()` + `_hadamard_multiplex()` — GPU/CuPy-Pfad muss hinter Feature-Flag bleiben; CPU-Fallback muss vorhanden sein.

---

### W6c — RadiBlohm Engine (Morphic Field, Quanten-Superposition)

Identisches Schema. Quelle: `radiquant4/apps/engines/radiblohm/`. Besonderheit: `calculate_morphic_field()` nutzt TCM-Elemente und Platonische-Körper-Faktoren — reine Python-Arithmetik, kein GPU nötig.

---

### W6d — RadiThoms Engine (5D-Vektor, Meridian-Balancen)

Identisches Schema. Quelle: `radiquant4/apps/engines/radithoms/`. Besonderheit: 12 Meridian-Balanzen + TCM-Elemente + Katastrophen-Theorie-Attraktoren. Zeitabhängige Meridian-Zyklen (24h-Uhr).

---

### W6e — RadiCopen Engine (Fibonacci-Raten, Level-Resonanz)

Identisches Schema. Quelle: `radiquant4/apps/engines/radicopen/`. Besonderheit: Adaptive Fibonacci-Paare, Kozyrev-Faktor (Entropy-Modulation), 13 Frequenz-Ebenen. Kein Hardware-Pfad.

**W6-Abschlussgate:** Cascade reviewed alle 5 PRs. Nach Merge: `pytest tests/ -q` → alle grün. `make verify` → grün.

---

## W7 — Synergy, Harmonization, Reports

### W7a — SynergyResult: Cross-Module-Synthese

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Vorbedingung** | W6 komplett ✅ |
| **Dateien** | `apps/api/app/schemas/synergy.py` (neu), `apps/api/app/services/synergy_service.py` (neu), `apps/api/app/routes/sessions.py` (ergänzen) |

**Genaue Änderungen:**

1. `SynergyResult` Schema: `session_id`, `tenant_id`, `confidence: float`, `modules_complete: list[str]`, `modules_pending: list[str]`, `conflicts: list[SynergyConflict]`, `consensus_summary: str`.
2. `SynergyConflict` Schema: `module_a`, `module_b`, `conflict_type`, `severity`.
3. `SynergyService.compute(session_id, tenant_id, db)`: lädt alle ModuleResults der Session, prüft Vollständigkeit, berechnet Confidence als `completed_modules / total_modules`, identifiziert Konflikte (z.B. polar entgegengesetzte Ergebnisse).
4. `GET /sessions/{id}/synergy` Endpunkt — gibt `SynergyResult` zurück. 404 wenn keine Ergebnisse.

**Akzeptanzkriterien:** Synergy korrekt tenant-scoped; Konflikte werden erkannt; Tests `tests/test_synergy_service.py` (min. 5)

---

### W7b — Harmonization Plan + Approval Gate

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Vorbedingung** | W7a ✅ |
| **Dateien** | `apps/api/app/schemas/harmonization.py` (neu), `apps/api/app/models/harmonization.py` (neu), `apps/api/app/routes/harmonization.py` (neu), Migration `0010_harmonization.py` (neu) |

**Genaue Änderungen:**

1. `HarmonizationPlan` Schema: `id`, `session_id`, `tenant_id`, `status` (draft/approved/rejected), `plan_payload_json`, `created_by_user_id`, `approved_by_user_id`, `approved_at`.
2. ORM `HarmonizationPlan` Modell.
3. Migration `0010_harmonization.py` — Tabelle `harmonization_plans`.
4. `POST /sessions/{id}/harmonization/plans` — erstellt Plan (status=draft).
5. `POST /sessions/{id}/harmonization/plans/{plan_id}/approve` — Therapeuten-Genehmigung (status=approved). **Niemals automatisch.**
6. `GET /sessions/{id}/harmonization/plans` — listet Pläne.

**Akzeptanzkriterien:** Plan ohne Approval nicht ausführbar. Approval-Event wird in event_log geschrieben. Tests min. 6.

---

### W7c — Harmonization Job: Pause/Resume/Stop

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Vorbedingung** | W7b ✅ |
| **Dateien** | `apps/api/app/models/harmonization.py` (ergänzen), `apps/api/app/services/harmonization_worker.py` (neu), `apps/api/app/routes/harmonization.py` (ergänzen) |

**Genaue Änderungen:**

1. `HarmonizationJob` ORM: `id`, `plan_id FK`, `tenant_id`, `status` (queued/running/paused/completed/failed/cancelled), `hardware_ack` (bool), `started_at`, `paused_at`, `completed_at`.
2. Worker `HarmonizationWorkerService`: `start(plan_id)`, `pause(job_id)`, `resume(job_id)`, `stop(job_id)`. Emittiert Events via EventWriter.
3. `POST /harmonization/jobs` — startet Job (requires approved plan).
4. `PATCH /harmonization/jobs/{id}/pause`, `/resume`, `/stop`.

**Hardware-ACK:** Worker wartet auf `hardware.ack`-Event vor Ausführung. Timeout → Hardware-Fallback.

**Akzeptanzkriterien:** Job nicht startbar ohne approved Plan. Pause/Resume korrekt. Hardware-Fallback bei Timeout.

---

### W7d — Reports: Client-Summary + Therapist-Appendix + Claim-Linter

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Vorbedingung** | W7c ✅ |
| **Dateien** | `apps/api/app/services/report_service.py` (neu), `apps/api/app/services/claim_linter.py` (neu), `apps/api/app/routes/reports.py` (neu) |

**Genaue Änderungen:**

1. `ClaimLinterService`: Prüft Report-Texte auf verbotene Formulierungen (`FORBIDDEN_CLAIM_PATTERNS`: "heilt", "behandelt", "diagnostiziert", "medizinisch", "klinisch", "garantiert"). Wirft `ClaimViolationError` mit Fundstellen.
2. `ReportService.build_client_report(session_id, tenant_id)`: Aggregiert Client-Projektion aller Engines, filtert alle technischen Keys, lässt durch Claim-Linter laufen. Output: `ClientReport` Schema.
3. `ReportService.build_therapist_appendix(session_id, tenant_id)`: Wie oben aber mit Therapist-Projektion + SynergyResult.
4. `GET /sessions/{id}/report?role=client|therapist` Endpunkt.

**Akzeptanzkriterien:** Claim-Linter schlägt an bei verbotenen Formulierungen. Client-Report enthält keine Rohdaten. Tests min. 8 (inkl. Claim-Linter-Unit-Tests).

---

## W8 — GDPR/Retention/Backup + Deployment-Baseline

### W8a — GDPR-Endpunkte: Export + Delete + Anonymize

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Vorbedingung** | W7 ✅ |
| **Dateien** | `apps/api/app/routes/gdpr.py` (neu), `apps/api/app/services/gdpr_service.py` (neu), `apps/api/app/main.py` |

**Endpunkte:**

1. `GET /clients/{id}/export` — vollständiger DSGVO-Datenexport als JSON: ClientProfile, Consents, Sessions, WorkflowRuns, ModuleResults, EventRecords (kein Raw-Debug). PII klar gekennzeichnet.
2. `DELETE /clients/{id}` — Anonymisierung (kein Hard-Delete): PII-Felder (`display_name`, `email` in verbundenen Usern) durch Pseudo-ID ersetzen, Consent-Status → `revoked`, Sessions → `anonymized`.
3. `POST /clients/{id}/retain` — explizite Verlängerung der Aufbewahrungsfrist (Audit-Log).

**Anforderungen:** Alle Operationen werden im Audit-Log aufgezeichnet. Tenant-Isolation obligatorisch. Keine Massen-Löschung ohne Bestätigung.

**Akzeptanzkriterien:** Export enthält alle Datenarten. Delete anonymisiert korrekt. Tests min. 8.

---

### W8b — Retention Policy + Cleanup-Service

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Vorbedingung** | W8a ✅ |
| **Dateien** | `apps/api/app/services/retention_service.py` (neu), Migration `0011_retention_policy.py` (neu) |

**Genaue Änderungen:**

1. `RetentionPolicy` ORM: `tenant_id`, `data_type` (sessions/events/module_results), `retention_days`, `enabled`.
2. `RetentionService.run_cleanup(tenant_id)`: Findet abgelaufene Datensätze per `retention_days`, anonymisiert (nicht löscht), schreibt Audit-Event.
3. CLI-Trigger: `python3 -m app.services.retention_service --tenant-id <UUID>`.

**Akzeptanzkriterien:** Cleanup korrekt tenant-scoped. Keine echten Löschungen ohne explizite DSGVO-Anfrage. Tests min. 5.

---

### W8c — Docker + Nginx + systemd Deployment

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI (Templates) + manuelles Review |
| **Vorbedingung** | W5c ✅ |
| **Dateien** | `infra/docker/docker-compose.yml` erweitern, `infra/docker/Dockerfile` (neu), `infra/nginx/nginx.conf` erweitern, `docs/ops/DEPLOYMENT.md` (neu) |

**Genaue Änderungen:**

1. `Dockerfile`: Multi-stage (builder + runtime). Python 3.11-slim. `pip install -e .` im Build-Stage. Non-root user.
2. `docker-compose.yml`: Services `api`, `db` (postgres:16 mit named volume), `nginx`. DB-Migrations beim Start via Alembic (`alembic upgrade head` als Entrypoint-Pre-Hook).
3. `docs/ops/DEPLOYMENT.md`: Schritt-für-Schritt: Clone → `docker-compose up -d` → erster Admin-User anlegen → Health-Check.

**Akzeptanzkriterien:**
- `docker build` ohne Fehler
- `docker-compose up -d` → alle Services healthy
- `GET /health` → 200 nach Start

---

### W8d — Prometheus-Metriken + Grafana-Dashboard + SLOs

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Vorbedingung** | W5c ✅, W8c ✅ |
| **Dateien** | `apps/api/app/routes/metrics.py` erweitern, `infra/monitoring/grafana-dashboards/radiquant-v5.json` (neu), `infra/monitoring/slo.yml` (neu) |

**Metriken:**

| Metrik | Typ | Labels |
|---|---|---|
| `http_requests_total` | Counter | method, path, status_code |
| `http_request_duration_seconds` | Histogram | method, path |
| `radi144_jobs_total` | Counter | status (queued/completed/failed) |
| `event_records_appended_total` | Counter | event_type |
| `sse_stream_requests_total` | Counter | role |
| `db_query_duration_seconds` | Histogram | operation |

**SLO-Definitionen (slo.yml):**
- API Availability: 99.5% (gemessen über `/health`)
- P95 Response Time: < 500ms
- Radi144 Job Success Rate: > 98%

**Grafana-Dashboard:** 6 Panels (HTTP-Rate, Latenz-Heatmap, Job-Status, Event-Throughput, SSE-Streams, DB-Latenz).

---

## W9 — Innovation Labs (feature-flagged, ab W8 stabil)

### W9a — Contract-Codegen-Pipeline (I-01)

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Dateien** | `apps/api/openapi.json` (generiert), `apps/web-astro/src/lib/api/schema.gen.ts` (generiert), CI-Gate erweitern |

OpenAPI aus FastAPI generieren (`/openapi.json` Endpunkt → Datei). TS-Client-Codegen via `openapi-typescript`. CI-Gate: `diff openapi.json` schlägt an bei Schema-Drift.

---

### W9b — HRV-gated Harmonization (I-06) [feature.hrv]

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Feature-Flag** | `feature.hrv = false` default |
| **Dateien** | `apps/api/app/services/hrv_gate.py` (neu), `apps/api/app/routes/harmonization.py` (ergänzen) |

`HRVGateService`: liest optionalen HRV-Input aus Session-Daten. Berechnet Kohärenz-Score. Harmonization-Job-Start blockiert wenn `hrv_coherence < threshold`. Fallback: Therapeuten-Override erlaubt.

---

### W9c — LLM Therapist-Copilot (I-08) [feature.llm_copilot]

| Feld | Wert |
|---|---|
| **Agent** | Codex CLI |
| **Feature-Flag** | `feature.llm_copilot = false` default |
| **Dateien** | `apps/api/app/services/llm_copilot.py` (neu) |

PII-Redaction vor LLM-Aufruf (via `EventRegistryService.FORBIDDEN_PAYLOAD_KEYS` + eigene PII-Patterns). Claim-Linter auf LLM-Output. Kein Heilversprechen. Alle LLM-Aufrufe auditiert.

---

### W9d — Adaptive Audio/Visual (I-09) [feature.adaptive_ux]

| Feld | Wert |
|---|---|
| **Agent** | Devin + Cascade (Review) |
| **Feature-Flag** | `feature.adaptive_ux = false` default |
| **Dateien** | `apps/web-astro/src/lib/chromotherapy/` (neu), `apps/web-astro/src/lib/audio/` (neu) |

Chromotherapie-Theme (Phasen-Farben aus workflow-chromotherapy), Circadian-Anpassung (5 Tagesphasen), binaure Beats (optional). WCAG-AAA Kontrast-Garantie. Alle Animationen `prefers-reduced-motion`-sicher.

---

## Verifikationsstandard (gilt für alle Wellen)

Jede Welle ist erst **abgeschlossen** wenn:

| Check | Befehl | Erwartung |
|---|---|---|
| Pytest | `pytest tests/ -q --tb=short` | 0 failed, 0 errors |
| mypy | `(cd apps/api && mypy app)` | no issues |
| verify | `make verify` | alle Gates grün |
| Frontend (ab W4) | `npm run test` in `apps/web-astro` | 0 failed |
| E2E (ab W4c) | `npx playwright test` in `apps/web-astro` | alle Flows grün |

---

## Agent-Zuordnungsmatrix (Gesamtübersicht)

| Ticket | Cascade | Codex CLI | Devin | Gemini |
|---|:--:|:--:|:--:|:--:|
| G-01 Governance-Bereinigung | Review | — | — | **Primär** |
| W3a SSE-Protokoll | Review | **Primär** | — | — |
| W3b has_more | Review | **Primär** | — | — |
| W3c Rollen-Projektion | Review | **Primär** | — | — |
| W3d Tests | Review | **Primär** | — | — |
| W4a Vitest | Review | **Primär** | — | — |
| W4b MVP-Seiten | Review | **Primär** | — | — |
| W4c Playwright | Review | **Primär** | optional | — |
| W4d A11y | Review | **Primär** | — | — |
| W5a Health | Review | **Primär** | — | — |
| W5b Admin-Routen | Review | **Primär** | — | — |
| W5c Ops-Baseline | Review | **Primär** | — | — |
| W6-ADR Scaffold | **Primär** | — | — | — |
| W6a–W6e Engines | Review + Fixes | Fixes | **Primär** | — |
| W7a–W7d Synergy/Harmonize/Reports | Review | **Primär** | — | — |
| W8a–W8d GDPR/Deploy/Monitoring | Review | **Primär** | — | — |
| W9a–W9d Labs | Review | **Primär** | W9d | — |

---

*Dokument automatisch erstellt von Cascade nach vollständiger Tiefenanalyse (2026-05-30).
Nächster ausführbarer Schritt: G-01 (Gemini) → W3a (Codex CLI).*
