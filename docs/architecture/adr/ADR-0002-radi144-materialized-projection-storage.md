# ADR-0002: Materialisierte Radi144-Projektionsspeicherung (eng begrenzte Freigabe)

## Status

Akzeptiert (2026-05-30). Ergänzt ADR-0001; hebt dessen Frozen-Status **ausschließlich**
für die hier benannte Einzelfähigkeit auf. Alle übrigen Frozen-Bereiche bleiben in Kraft.

## Kontext

ADR-0001 hat die rekursive Decision-Gate-Kaskade eingefroren. Teil dieser Kaskade
waren zahlreiche `*_materialized_projection_*_decision`-Tripwires, die die
materialisierte Speicherung von Radi144-Projektionen hinter Vorentscheidungen
blockierten (jetzt unter `archive/decision_gate_cascade/`).

Ist-Zustand der Engine Radi144:
- Migration `0007_engine_result_storage` legt `ModuleRun` / `ModuleResult` /
  `ModuleProvenance` an.
- `app/services/radi144/result_writer.py` persistiert validierte Ergebnisse
  tenant-scoped mit `projection_status = "pending_projection_builder"`.
- `app/services/radi144/projection_builder.py` baut rollensichere Client-/
  Therapist-Projektionen, ist aber **nur in-memory** und „not wired to API routes,
  frontend UI, workers, or engine execution".

Damit liefert Radi144 noch keinen echten End-to-End-Nutzwert: Ergebnisse werden
gespeichert, die für Therapeut/Klient lesbaren Projektionen aber bei jedem Lesen neu
berechnet bzw. gar nicht bereitgestellt. W2 (Wellenplan) verlangt den ersten echten
vertikalen Nutzwert.

## Entscheidung

Wir tauen **genau eine** Fähigkeit bewusst und eng begrenzt auf:
**die materialisierte, tenant-scoped Speicherung der Radi144-Rollenprojektionen.**

Freigegebener Scope (und nur dieser):
1. Neue Tabelle `module_projections` via Migration `0008_module_projections` (up/down).
2. ORM-Modell `ModuleProjection` in `app/models/engine.py`.
3. Ein Projection-Write-/Materialisierungs-Service, der aus einem bereits
   gespeicherten `ModuleResult` die Client- **und** Therapist-Projektion über den
   bestehenden `Radi144ProjectionBuilder` erzeugt und **idempotent** speichert.
4. Verdrahtung der Worker-Materialisierung (nach Result-Write → Projektion
   materialisieren) im bestehenden CPU-Worker-Pfad.
5. Der bestehende API-Lesepfad liefert die **materialisierte** Projektion.

## Abgrenzung (bleibt eingefroren)

Dieser ADR reaktiviert **nicht**:
- die rekursive Decision-Gate-Kaskade oder neue `*_decision`-Tripwire-Skripte/-Tests;
- Radi144 GPU/CUDA-Compute;
- API-getriggerte Engine-Ausführung;
- externe Queue/Daemon-Ausführung.

Diese bleiben gemäß ADR-0001 blockiert und benötigen jeweils einen eigenen ADR.

## Leitplanken

- **Sicherheit:** Es gelten unverändert die bestehenden Guards (verbotene Schlüssel,
  `wellbeing_only`-Sprache, `raw_debug` ausgeschlossen). Projektionen dürfen keine
  Roh-/Debug-/Internalfelder enthalten.
- **Tenant-Isolation:** Alle Lese-/Schreibzugriffe sind strikt tenant-scoped.
- **Idempotenz:** Wiederholte Materialisierung darf nicht duplizieren —
  `UNIQUE(tenant_id, module_run_id, role)`.
- **Echte Tests:** Funktionstests prüfen reales Verhalten (materialisiert, lesbar,
  isoliert), nicht die bloße Abwesenheit („absent"-Tests werden ersetzt).
- **Minimal-invasiv:** Bestehende Services (`result_writer`, `projection_builder`,
  Worker-Runtime) werden verdrahtet, nicht ersetzt.

## Konsequenzen

- Migrations-Baseline wächst um `0008`; neues ORM, neuer Service, Worker-Verdrahtung
  und neue Funktionstests kommen hinzu.
- Radi144 liefert erstmals einen echten E2E-Pfad: Ausführung → Result-Write →
  Projektions-Materialisierung → rollensicheres Lesen.
- Dies ist ein **einmaliger, begrenzter** Unfreeze. Jede weitere Fähigkeit aus dem
  Frozen-Set erfordert einen neuen ADR.

## Referenz

- Vorgänger: `ADR-0001-decision-gate-cascade-frozen.md`
- Welle: `docs/umsetzungsplan/02_UMSETZUNGSPLAN_WELLEN.md` → W2
- Adressierte Lücken: P-02, P-08, P-09
