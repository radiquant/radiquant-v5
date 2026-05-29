# SYSTEM_STATE — radiquant-v5 (lebendes Status-Dokument)

> Single Source of Truth für den **aktuellen** Ist-Zustand des v5-Rebuilds.
> Onboarding/Decisions: siehe `README.md` und `docs/architecture/START_HERE.md`.
> Detailplanung (historisch): `/opt/radiquant4/docs/restart-radiquant-v5/`.

## 1. Überblick
- **Projekt:** Kontrollierter Ground-Zero-Rebuild der Radiquant-Wellbeing-Plattform.
- **Referenz-Repo:** `/opt/radiquant4`.
- **Phase:** 5 — Auth/Tenant/Audit-DB-Metadaten + initiale Migration.
- **Stack:** FastAPI / Python 3.11 · Astro SSR + React Islands / Node 22 · PostgreSQL · Redis.
- **Architektur:** Modularer Monolith + Worker. Erstes Vertical Engine: **Radi144** (unter `apps/api/app/services/radi144/`). Weitere Engines (RadiWorks/RadiMorphic/RadiBlohm/RadiThoms/RadiCopen) noch **nicht** in v5 implementiert.

## 2. Repo-Layout (Ist)
- `apps/api/` — FastAPI-App, Services, Models, Routes, Alembic.
- `apps/web-astro/` — Frontend (Astro + React Islands).
- `packages/contracts/` — Contract-Schemas/Instances (Daten-SSOT).
- `scripts/` — Verify-Gates (`verify_bootstrap.py`).
- `tests/` — pytest-Suite (21 Testdateien).
- `docs/` — Architektur-Docs + ADRs.
- `archive/decision_gate_cascade/` — eingefrorene Decision-Tripwires (siehe §5).

## 3. Verifikation
- **Gates:** `make verify` -> `scripts/verify_bootstrap.py` (182 `[OK]`-Gates, grün).
- **Tests:** `python3 -m pytest -p no:cacheprovider -q` (grün).
- **Timeout-Netz:** `pyproject.toml [tool.pytest.ini_options]` `timeout=60`, `timeout_method="thread"` — Hänger werden zu Fehlern statt Endlos-Blockade.

## 4. Kritischer Verifikations-Caveat (Codex-Sandbox)
`make verify` / `pytest` **NICHT** innerhalb der Codex-CLI-Sandbox ausführen.
Die `codex-linux-sandbox` triggert einen **intermittierenden Deadlock** in async-Generator-Fixtures (`pytest-asyncio 1.3.0` + `aiosqlite`-Worker-Thread). Auf dem **normalen Host** ist die Suite stabil grün (>13 Läufe bestätigt).
**Regel:** Code-Edits via Codex CLI, **Verifikation im Plain-Terminal** (oder durch den Host-Verifier).

## 5. Decision-Gate-Kaskade — EINGEFROREN
Die frühere rekursive Precondition-Kaskade (77 Check-Skripte + 76 Tests) ist eingefroren — siehe `docs/architecture/adr/ADR-0001-decision-gate-cascade-frozen.md`.
- Skripte + Tests -> `archive/decision_gate_cascade/` (aus `verify`/`pytest` herausgelöst).
- Zugehörige `docs/architecture/*_DECISION_GATE.md` + `packages/contracts/**`-Schemas/Instances bleiben als **Daten-SSOT** erhalten, sind aber als "frozen" zu lesen.
- Neue Decision-Gates nur mit neuem ADR.

## 6. W0-Stabilisierung — Changelog
| Commit | Inhalt |
|---|---|
| `cfb7156` | Git-Baseline (603 getrackte Dateien). |
| (Härtung) | pytest-timeout-Netz; `StaticPool`+`check_same_thread` für In-Memory-aiosqlite via `make_async_engine`; `asyncio_default_fixture_loop_scope="function"`. |
| `8160938` | Decision-Gate-Kaskade eingefroren (Archiv + verify-Pruning + ADR-0001). |
| `f10a027` | 109 tote `REQUIRED_FILES`/`REFERENCE_FILES`-Einträge entfernt; `make verify` wieder grün. |

## 7. Bekannte Restschuld (nicht blockierend)
- Finaler `print` in `scripts/verify_bootstrap.py` zählt noch ~100 eingefrorene Decision-Gates als "present" auf (rein kosmetisch).
- `AGENTS.md` §5 verweist auf historische `SYSTEM_STATE.md (v10.0)` / `UMSETZUNGSPLAN.md` aus dem v4-Repo; diese Datei ist die maßgebliche v5-Statusquelle.

## 8. Nächste Schritte
- W0 abschließen, dann Folge-Wellen gemäß `/opt/radiquant4/docs/restart-radiquant-v5/08_OPTIMAL_REBUILD_SEQUENCE.md`.

---
*Stand: 2026-05-29. Bei jeder substanziellen Änderung aktualisieren.*
