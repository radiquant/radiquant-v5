# SYSTEM_STATE — radiquant-v5 (lebendes Status-Dokument)

> Single Source of Truth für den **aktuellen** Ist-Zustand des v5-Rebuilds.
> Onboarding/Decisions: siehe `README.md` und `docs/architecture/START_HERE.md`.
> **Umsetzungsplan + lebender Fortschritt (in-repo SSOT):** `docs/umsetzungsplan/` (README + Wellenplan W0–W9 + `05_FORTSCHRITT_LOG.md`).
> Detailplanung/Analyse-Ursprung (historisch, radiquant4): `/opt/radiquant4/docs/restart-radiquant-v5/`.

## 1. Überblick
- **Projekt:** Kontrollierter Ground-Zero-Rebuild der Radiquant-Wellbeing-Plattform.
- **Referenz-Repo:** `/opt/radiquant4`.
- **Phase:** 5 — Auth/Tenant/Audit-DB-Metadaten + initiale Migration.
- **Stack:** FastAPI / Python 3.11 · Astro SSR + React Islands / Node 22 · PostgreSQL · Redis.
- **Architektur:** Modularer Monolith + Worker. Erstes Vertical Engine: **Radi144** (unter `apps/api/app/services/radi144/`). Weitere Engines (RadiWorks/RadiMorphic/RadiBlohm/RadiThoms/RadiCopen) noch **nicht** in v5 implementiert.

## 2. Repo-Layout (Ist)
- `apps/api/` — FastAPI-App, Services, Models, Routes, Alembic.
- `apps/web-astro/` — Frontend-Stub (Astro + React Islands geplant; **noch keine Node-Deps deklariert**, nicht baubar — Schuld S-01).
- `packages/contracts/` — Contract-Schemas/Instances (Daten-SSOT).
- `scripts/` — Verify-Gates (`verify_bootstrap.py`).
- `tests/` — pytest-Suite (21 Testdateien).
- `docs/` — Architektur-Docs + ADRs + `docs/umsetzungsplan/` (Plan + Fortschritts-Log).
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
| `4518896` | Lebendes `SYSTEM_STATE.md` angelegt (W0-03). |
| `085e03b` | Kosmetisches Cleanup (verify-`print` gekürzt) — W0 versiegelt. |

## 6b. W1 — CI-Pipeline (Changelog)
| Schritt | Inhalt |
|---|---|
| W1a | `[project.dependencies]` (13 Runtime, exakt gepinnt) + `dev` (5 Tools) in `pyproject.toml`. |
| W1a-fix | `[build-system]` + `[tool.setuptools] py-modules = []` → reproduzierbarer deps-only `pip install -e ".[dev]"` trotz Flat-Layout. **Verifiziert:** Frisch-venv install + `pytest` 121 passed + `mypy` sauber + `make verify` grün. |
| W1b | `.github/workflows/ci.yml` — offen. |

## 7. Bekannte Restschuld (nicht blockierend)
- **S-01:** Root `package.json` ohne Node-Deps; `apps/web-astro` nicht baubar → W1c/W4.
- **S-02:** ~100 tote `check:*decision*`-npm-Scripts in `package.json` → Cleanup W1b/W1c.
- **S-03:** `make verify` führt ruff/mypy/typecheck noch nicht real aus (nur Bootstrap) → Gates via CI (W1b).
- Details/Tracking: `docs/umsetzungsplan/05_FORTSCHRITT_LOG.md` (Abschnitt „Bekannte Schuld").

## 8. Nächste Schritte
- **W1b:** `.github/workflows/ci.yml` (pytest + mypy + `make verify` blockierend; ruff informativ; secret-scan). Dann W2 (Radi144 echtes E2E).
- Verbindlicher Plan + jeweils aktueller Status: `docs/umsetzungsplan/05_FORTSCHRITT_LOG.md`.

---
*Stand: 2026-05-30. Bei jeder substanziellen Änderung aktualisieren.*
