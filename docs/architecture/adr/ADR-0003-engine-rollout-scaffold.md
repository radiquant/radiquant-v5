# ADR-0003: Engine-Rollout Scaffold & Migrations-Richtlinien

## Status

Akzeptiert (2026-05-31). Ergänzt den Umsetzungsplan W6.

## Kontext

Das Projekt `radiquant-v5` muss fünf weitere Kern-Engines aus `radiquant4` portieren: RadiWorks, RadiMorphic, RadiBlohm, RadiThoms, und RadiCopen. 
Um sicherzustellen, dass die Migration dieser komplexen Module konsistent, testbar und rollensicher abläuft (Tenant-Isolation, Result-Projektionen), benötigen wir einen verbindlichen Architektur-Scaffold (Schablone), an den sich autonome Agenten (wie Devin) strikt halten müssen. Die Muster aus `Radi144` (W2) dienen als Blaupause.

## Entscheidung

Wir definieren einen verbindlichen Scaffold für jede neu zu portierende Engine. Die Umsetzung erfolgt inkrementell (eine Engine pro PR) unter folgenden Leitplanken:

### 1. Kanonisches Datei-Layout

Für die fiktive Engine `radixxx` müssen exakt diese Strukturen erzeugt werden:

- **Migration**: `apps/api/alembic/versions/XXXX_radixxx_results.py`
  - Tabelle: `radixxx_results`
  - Spalten: `tenant_id` (UUID, Index), `module_run_id` (UUID, PK/FK), `result_payload_json` (JSONB), `projection_status` (VARCHAR).
  - *Hinweis:* Auch Materialisierungstabellen (z. B. `radixxx_projections`) sind gestattet, analog zu ADR-0002.

- **ORM-Modell**: `apps/api/app/models/radixxx.py`
  - Klasse `RadiXxxResult` (bzw. `RadiXxxProjection`).

- **Services**: `apps/api/app/services/radixxx/`
  - `engine.py` (Kern-Algorithmus portiert aus rq4)
  - `result_writer.py` (Idempotenter DB-Writer)
  - `projection_builder.py` (Tenant-/Rollensichere Sicht auf Ergebnisse)
  - `worker_runtime.py` (Celery/Async-Worker-Integration, analog zu `Radi144WorkerRuntime`)

- **Routen**: `apps/api/app/routes/radixxx.py`
  - `POST /engines/radixxx/jobs` (Trigger)
  - `GET /engines/radixxx/jobs/{id}` (Status)
  - `GET /engines/radixxx/jobs/{id}/result` (mit `?role=` Projektion)

- **Schemas**: `apps/api/app/schemas/radixxx.py`
  - Pydantic-Modelle für API-Request, Result-Payload und Rollen-Projektionen.

- **Tests**: `apps/api/tests/test_radixxx_*.py`
  - `test_radixxx_engine.py` (Domain-Logik)
  - `test_radixxx_worker.py` (Worker-Runtime)
  - `test_radixxx_api.py` (Tenant- und Rollen-Isolation!)

### 2. Algorithmus-Port-Richtlinien

1. **Kein Copy-Dump:** Der Python-Code aus `radiquant4/apps/engines/radixxx/` darf nicht unreflektiert kopiert werden. Er muss in das typisierte, moderne FastAPI-v5-Layout überführt werden.
2. **Hardware-Entropie stubben:** Da W6 vor der physischen Hardware-Migration (W8/W9) stattfindet, muss hardware-abhängige Entropie (Kozyrev, QRNG) gestubbt werden (z. B. durch deterministische Seeds oder `os.urandom`), falls das Feature-Flag `RQ5_HARDWARE_ENTROPY` = `false` ist.
3. **GPU-Flagging:** CuPy/CUDA-Pfade (z. B. in RadiMorphic) MÜSSEN hinter einem Feature-Flag (z. B. `RQ5_KOZYREV_GPU`) liegen. Ein funktionierender reiner CPU-Fallback (`numpy`) ist zwingend.

### 3. Tenant-Isolation & Sicherheit

- **Strikte Mandantentrennung:** Alle Services und Routen müssen `TenantContext` durchgängig verwenden. Kein SQL-Select darf ohne `where(tenant_id == ...)` ausgeführt werden.
- **Rollen-Projektion:** `result_payload_json` ist die Single Source of Truth (enthält alle Debug-/Rohdaten). Die API darf diese NIE direkt ausliefern. Der `projection_builder` muss die Rohdaten in rollenspezifische Sichten (`client`, `therapist`, `admin`) filtern, bevor sie materialisiert oder gesendet werden (Ausblenden von Metriken, internen Scores).

### 4. Rollback-Strategie

- Jede Engine wird in einem isolierten Feature-Branch (z. B. `feature/w6a-radiworks`) entwickelt.
- Die Alembic-Migration muss eine funktionierende `downgrade()`-Methode aufweisen.
- Der Master-Branch wird erst gemerged, wenn die Pytest-Coverage für die Domain-, Worker- und API-Schicht der jeweiligen Engine >= 90% liegt und keine bestehenden Tests brechen (`pytest -v`).

## Konsequenzen

- Autonome Agenten haben einen klaren, einklagbaren Contract für ihre PRs.
- Code-Reviews (durch den Architekten Cascade oder den User) fokussieren sich auf die Einhaltung dieses Scaffolds.
- Die v5-Architektur bleibt homogen; alle Engines verhalten sich im Runtime-Tracker, im API-Gate und in der DB identisch zu Radi144.

## Referenzen

- Vorgänger: `ADR-0002` (Materialisierte Radi144-Projektionen)
- Welle: `docs/umsetzungsplan/06_VOLLPLAN_W3_W9_DETAILLIERT.md` (W6)
