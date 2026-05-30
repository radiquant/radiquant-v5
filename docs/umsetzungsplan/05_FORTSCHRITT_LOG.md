# 05 — Fortschritts-Log radiquant-v5 (lebend)

> **Zweck:** Entwicklerseitige Single Source of Truth für den Umsetzungsfortschritt **innerhalb** von `/opt/radiquant-v5`.
> **Pflege:** Nach jedem verifizierten Schritt fortschreiben — Status, Commit, Verifikationsbeleg.
> **Legende:** ✅ erledigt+verifiziert · 🔄 in Arbeit · ⏳ offen · ⛔ blockiert
>
> **Arbeitszyklus (fix):** Cascade plant copy-paste-fertige Schritte → Codex CLI führt **Code-Edits** aus → Verifikation (`pytest`/`make verify`/`mypy`/`pip install`) läuft in **normalem Terminal** (nicht in der Codex-Sandbox, dort intermittierender aiosqlite/pytest-asyncio-Deadlock) → Cascade prüft Output → grün = nächster Schritt. Details: `03_CODEX_CLI_INTEGRATION.md`.

---

## Wellen-Statusübersicht

| Welle | Inhalt | Status | Belegt durch |
|---|---|---|---|
| **W0** | Stabilisierung & Git-Baseline | ✅ | Commits `cfb7156`→`085e03b` |
| **W1** | CI-Pipeline (PR-Gates) | ✅ (Config) | W1a/W1a-fix/W1b ✅; auf GitHub aktiv, Runs durch Org-Billing blockiert (extern) |
| **W2** | Radi144 vertikaler Nutzwert (echtes E2E) | 🔄 | ADR-0002 akzeptiert; W2a ⏳ |
| **W3** | Realtime & Result-Projektionen | ⏳ | — |
| **W4** | Frontend-Test-Harness + MVP-Demo | ⏳ | — |
| **W5** | Minimal Admin/Ops | ⏳ | — |
| **W6** | Engine-Rollout 2–6 (Devin) | ⏳ | — |
| **W7** | Synergy, Harmonization, Reports | ⏳ | — |
| **W8** | GDPR/Retention/Backup + Deployment | ⏳ | — |
| **W9** | Innovation Labs (feature-flagged) | ⏳ | — |

---

## W0 — Stabilisierung & Git-Baseline ✅

| Ticket | Inhalt | Status | Commit |
|---|---|---|---|
| W0-01 | Git-Baseline (initialer Commit, `.gitignore`) | ✅ | `cfb7156` |
| W0-02 | Decision-Gate-Kaskade eingefroren (Skripte/Tests/Docs → `docs/_archive/`, ADR-0001) | ✅ | `8160938` |
| W0-02b | `verify_bootstrap.py` von archivierten Decision-Pfaden bereinigt (Required-File-Listen) | ✅ | `f10a027` |
| W0-03 | Lebendes `SYSTEM_STATE.md` angelegt | ✅ | `4518896` |
| W0-04 | Kosmetisches Cleanup (Rest-Decision-Enumeration im finalen Print gekürzt) | ✅ | `085e03b` |

**Härtung (in W0 angewandt, bleibt aktiv):**
- `pytest-timeout` (timeout=60, timeout_method="thread") in `pyproject.toml` → Hänger werden zu Fehlern.
- `StaticPool` + `check_same_thread=False` für In-Memory-aiosqlite über `make_async_engine` in `apps/api/app/db/session.py`.
- `asyncio_default_fixture_loop_scope = "function"`.

**ADR:** `docs/architecture/adr/ADR-0001-decision-gate-cascade-frozen.md` — Radi144 GPU/CUDA, API-getriggerte Ausführung, externe Queue/Daemon-Ausführung und materialisierte Projektionsspeicherung bleiben blockiert, bis ihre Gates explizit geöffnet werden.

---

## W1 — CI-Pipeline (PR-Gates) 🔄

**Ziel:** Anti-Drift-Gates laufen automatisch bei jedem PR. Adressiert P-03.

**Vorbedingung entdeckt (2026-05-30):** Weder Python noch Node hatten deklarierte Dependencies → Projekt nicht reproduzierbar installier-/baubar → CI auf frischem Runner unmöglich. W1 daher in W1a (Deps-Manifest) + W1b (ci.yml) geteilt; Frontend-Typecheck verschoben (siehe unten).

| Ticket | Inhalt | Status | Beleg |
|---|---|---|---|
| W1a | `[project.dependencies]` (13 Runtime, exakt gepinnt) + `dev` (5 Tools) in `pyproject.toml` | ✅ verifiziert | siehe Verifikation unten |
| W1a-fix | `[build-system]` + `[tool.setuptools] py-modules = []` → deps-only Editable-Install trotz Flat-Layout (apps/infra/archive/packages) | ✅ verifiziert | siehe Verifikation unten |
| W1b | `.github/workflows/ci.yml`: pytest + mypy + `make verify` (blockierend), ruff (informativ), secret-scan (gitleaks-Action) | ✅ lokal validiert | YAML gültig, keine cci-Links, Gate-Befehle grün; Live-Lauf bei Push |
| W1c | Node/Frontend-Deps deklarieren + Frontend-Typecheck-Gate (verschoben, siehe Schuld) | ⏳ | — |

**Offener externer Punkt (kein Code):** GitHub-Actions-Runs der Org `radiquant` sind durch Billing/Spending-Limit gesperrt („job was not started … payments have failed“). Fix: Org → Billing & plans (Zahlungsmethode/Limit) **oder** Repo public (unbegrenzte Free-Minuten). Danach `Re-run jobs` auf `2566c57`. Workflow-Datei-Änderungen müssen bis zur PAT/OAuth-Policy-Freigabe über die Web-UI erfolgen.

## W2 — Radi144 echtes E2E (via ADR-0002) 🔄

**Governance:** `docs/architecture/adr/ADR-0002-radi144-materialized-projection-storage.md` — einmaliger, eng begrenzter Unfreeze der materialisierten Projektionsspeicherung. Frozen bleiben: rekursive Decision-Kaskade, GPU/CUDA, API-getriggerte Ausführung, externe Queue/Daemon.

| Ticket | Inhalt | Status |
|---|---|---|
| W2a | Migration `0008_module_projections` (up/down) + ORM `ModuleProjection` (`module_projections`, `UNIQUE(tenant_id, module_run_id, role)`) | ✅ (120 passed, mypy sauber, verify grün) |
| W2b | Projection-Materialisierungs-Service: aus `ModuleResult` via `Radi144ProjectionBuilder` Client+Therapist materialisieren, idempotent, tenant-scoped | ⏳ |
| W2c | Worker-Verdrahtung: nach Result-Write → Projektion materialisieren (CPU-Worker-Pfad) | ⏳ |
| W2d | Funktionstests (echtes Verhalten: materialisiert/lesbar/tenant-isoliert/idempotent) + API-Lesepfad auf materialisierte Projektion | ⏳ |

**Design-Leitplanke:** `ModuleResult`-CHECK nagelt `projection_status='pending_projection_builder'` fest → Materialisierung wird **nicht** über das alte Feld, sondern über die neue Tabelle `module_projections` abgebildet (minimal-invasiv, keine SQLite-CHECK-Alter-Komplexität). Idempotenz via `UNIQUE(tenant_id, module_run_id, role)`.

**W2a-Cleanup (Cascade, ADR-0002):** Der Frozen-Era-Gate `check_radi144_projection_gate_ergonomics` erzwang aktiv die Abwesenheit von `module_projections`/`ModuleProjection` und kollidierte direkt mit ADR-0002. Nach ADR-0001-Muster retiriert: Validator + Test nach `archive/decision_gate_cascade/` verschoben, aus `verify_bootstrap.py` (Aufruf + 2 REQUIRED_FILES-Einträge) gelöst, verify-Abschlussmeldung ADR-0002-konform aktualisiert.

**Governance-Schuld G-01 (entdeckt):** `scripts/validate_contracts.py` enthält eine große, nicht archivierte Radi144-Decision-Kaskade (~Z. 2000–2142), die per `project.yml`-Anker erzwingt, dass Result-Persistence/Projection-Builder/Materialisierung/GPU „disabled/absent" bleiben. Aktuell **grün** (prüft nur Anker, nicht Code), wird aber spätestens in W2c (Runtime-Verdrahtung) kollidieren. Muss dann unter ADR-0002 (ggf. Scope-Erweiterung) governiert bereinigt werden — **nicht** ad hoc.

**Deklarierte Runtime-Deps (exakt gepinnt, = installierte Baseline):**
`fastapi==0.128.0`, `uvicorn==0.40.0`, `pydantic==2.12.5`, `pydantic-settings==2.12.0`, `sqlalchemy==2.0.45`, `greenlet==3.3.0`, `alembic==1.17.2`, `asyncpg==0.31.0`, `aiosqlite==0.22.1`, `pyjwt==2.6.0`, `python-multipart==0.0.21`, `email-validator==2.3.0`, `httpx==0.28.1`.
**Dev-Deps:** `pytest==9.0.2`, `pytest-asyncio==1.3.0`, `pytest-timeout==2.4.0`, `ruff==0.14.10`, `mypy==1.19.1`.

**Verifikation W1a/W1a-fix (Frisch-Install aus Null, normales Terminal):**
```
python3 -m venv /tmp/v5venv && . /tmp/v5venv/bin/activate
pip install -e ".[dev]"     # alle 13+5 Deps sauber installiert
pytest                       # 121 passed (kein Deadlock)
(cd apps/api && mypy app)    # Success: no issues found in 51 source files
make verify                  # alle aktiven Gates grün
```

**CI-Gate-Politik (für W1b festgelegt):**
- **Blockierend:** `pytest`, `mypy apps/api` (Baseline sauber), `make verify` (Bootstrap/Drift). CI läuft auf GitHub-Runnern (nicht Codex-Sandbox) → kein aiosqlite-Deadlock.
- **Informativ (nicht blockierend, vorerst):** `ruff check .` — aktuell ~5757 Altlast-Findings (Regelsatz E,F,I,UP,B,SIM). Hart-Gating erst nach separater Cleanup-Welle.
- **Secret-Scan:** `gitleaks` via GitHub-Action (kein lokaler Install nötig).

---

## Bekannte Schuld / Verschobenes

| ID | Thema | Plan |
|---|---|---|
| S-01 | Root `package.json` ohne `dependencies`/`devDependencies`; `apps/web-astro` ist nicht-baubarer Stub | W1c / W4: echte Node-Deps deklarieren, dann Frontend-Typecheck + Build-Gate |
| S-02 | `package.json` enthält noch ~100 tote `check:*decision*`-npm-Scripts (Verweise auf archivierte Skripte) | Cleanup im Zuge von W1b/W1c (Kernset reduzieren) |
| S-03 | `make verify` führt noch keine ruff/mypy/typecheck real aus (nur Bootstrap) | W1b: Gates in CI; optional `make verify` erweitern, sobald ruff grün |

---

## Änderungshistorie dieses Logs

| Datum | Eintrag |
|---|---|
| 2026-05-30 | Log angelegt; W0 als versiegelt dokumentiert; W1a/W1a-fix verifiziert (121 passed, mypy sauber, make verify grün); W1b/W1c/Schuld erfasst. |
| 2026-05-30 | W1b: `.github/workflows/ci.yml` angelegt (backend blockierend, lint informativ, secret-scan); lokal validiert (YAML, cci-frei, Gate-Befehle grün). Live-CI-Lauf erfolgt beim ersten Push nach GitHub. |
| 2026-05-30 | Repo nach `github.com/radiquant/radiquant-v5` gepusht. Hinweis: Workflow-Push via Git scheiterte an Org-OAuth/PAT-Policy → `ci.yml` per Web-UI angelegt/verschoben (`.github/workflows/ci.yml`, Commit `2566c57`). GitHub-Actions-**Runs** sind durch ein **Org-Billing-Problem** blockiert (extern, kein Code-Defekt) — Config korrekt, läuft nach Billing-Fix per Re-run. Lokale Gates bleiben maßgeblich. |
| 2026-05-30 | W2 gestartet: **ADR-0002** akzeptiert (eng begrenzter Unfreeze der materialisierten Radi144-Projektionsspeicherung). Nächster Schritt W2a (Migration 0008 + `ModuleProjection`-ORM). |
| 2026-05-30 | **W2a ✅** (Codex): ORM `ModuleProjection` + Migration `0008_module_projections` (up/down) + Export. Cascade-Cleanup: obsoleten `projection_gate_ergonomics`-Gate retiriert (→ archive). Verifikation: **120 passed**, mypy sauber, `make verify` grün. Governance-Schuld **G-01** (validate_contracts.py Radi144-Kaskade) erfasst. Kein Push (Workflow-frei; via origin nach Bedarf). |
