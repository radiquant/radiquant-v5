# 02 — Umsetzungsplan in Wellen (lückenlos, agentenzugeordnet)

> **Stand:** 2026-05-29 · Jede Welle: Ziel, Primäragent, Arbeit, Akzeptanz, Verifikation, Commit.
> **Grundregel:** Keine Welle gilt als fertig ohne grünes `make verify` + `pytest` + Commit.

---

## W0 — Stabilisierung & Git-Baseline (Blocker-Befreiung)

| Feld | Inhalt |
|---|---|
| **Ziel** | v5 lieferfähig machen: Git-Historie, Schleife stoppen, verify härten |
| **Primär** | Cascade (Plan/Review) + Codex CLI (Ausführung) |
| **Arbeit** | 1) `.gitignore` prüfen, initialen Commit setzen. 2) Decision-Gate-Kaskade einfrieren: eine ADR „Materialized Projection" erstellen, 59+ Gate-Docs/Tests/Skripte nach `docs/_archive/` verschieben. 3) `make verify` um `ruff check`, `mypy apps/api`, `npm run typecheck` erweitern. 4) npm-Scripts auf Kernset reduzieren. 5) `project.yml` auf schlanken Anker kürzen. |
| **Akzeptanz** | `git log` zeigt Baseline; `make verify` führt Lint/Typecheck real aus; `project.yml` < 5 KB; Decision-Skripte nicht mehr im aktiven Pfad |
| **Verifikation** | `make verify && pytest && ruff check . && mypy apps/api` grün |
| **Adressiert** | P-01, P-02, P-04, P-06, P-07 |

## W1 — CI-Pipeline (PR-Gates)

| Feld | Inhalt |
|---|---|
| **Ziel** | Anti-Drift-Gates laufen automatisch bei jedem PR |
| **Primär** | Codex CLI (Design: Cascade) |
| **Arbeit** | `.github/workflows/ci.yml`: Jobs pytest, ruff, mypy, frontend-typecheck, `make verify` (Route-/OpenAPI-Drift), secret-scan |
| **Akzeptanz** | CI grün auf Baseline; PR ohne grüne CI nicht mergebar |
| **Verifikation** | CI-Run grün |
| **Adressiert** | P-03 |

## W2 — Radi144 vertikaler Nutzwert (echtes E2E)

| Feld | Inhalt |
|---|---|
| **Ziel** | Erste Engine end-to-end mit echtem Nutzwert (statt Governance) |
| **Primär** | Codex CLI (Review: Cascade) |
| **Arbeit** | `0008_module_projections.py` real (up/down), ORM `ModuleProjection`, Projection Write Service, Worker-Materialisierung mit Idempotenz, Funktionstests (kein „absent"-Test) |
| **Akzeptanz** | Migration up/down getestet; Result wird materialisiert; Tenant-Isolation grün; Funktionstests prüfen echtes Verhalten |
| **Verifikation** | `pytest` (neue Funktionstests) + `make verify` grün |
| **Adressiert** | P-02, P-08, P-09 |

## W3 — Realtime & Result-Projektionen

| Feld | Inhalt |
|---|---|
| **Ziel** | Echter Live-Fortschritt + saubere Rollenprojektion |
| **Primär** | Codex CLI |
| **Arbeit** | SSE mit Replay-Cursor + Backoff + Polling-Fallback; UI-State connected/reconnecting/fallback/offline; Client Summary vs. Therapist Detail vs. Admin Debug |
| **Akzeptanz** | Reconnect/Replay-Demo; Client sieht keine Rohdaten; Realtime-Event-Tests grün |
| **Verifikation** | Realtime-Tests + Projektionstests grün |
| **Adressiert** | P-10 |

## W4 — Frontend-Test-Harness + MVP-Demo

| Feld | Inhalt |
|---|---|
| **Ziel** | Frontend testbar + vollständige vertikale Demo |
| **Primär** | Codex CLI (Devin optional für Test-Suite) |
| **Arbeit** | Vitest (Islands/Hooks) + Playwright (Login→Klient→Consent→Session→Radi144→Result→Views); A11y-Smoke (Kontrast, Keyboard, reduced motion) |
| **Akzeptanz** | MVP-Demo aus `07_MVP_GATES_AND_ACCEPTANCE.md` end-to-end grün |
| **Verifikation** | `npm run test` (vitest) + Playwright-Lauf grün, in CI |
| **Adressiert** | P-05, P-09 |

## W5 — Minimal Admin/Ops

| Feld | Inhalt |
|---|---|
| **Ziel** | Echte Health-/Status-Sicht, keine toten URLs |
| **Primär** | Codex CLI |
| **Arbeit** | Health-API (DB/Redis/Worker/Eventstream), Route-Manifest-Status, Audit-Browser minimal |
| **Akzeptanz** | Admin Health zeigt echte Daten; alle Admin-URLs contract-gebunden |
| **Verifikation** | API-/Smoke-Tests grün |

## W6 — Engine-Rollout 2–6 (breit, autonom)

| Feld | Inhalt |
|---|---|
| **Ziel** | RadiWorks→RadiCopen nach Radi144-Muster |
| **Primär** | **Devin** (Review: Cascade, Fixes: Codex CLI) |
| **Arbeit** | Pro Engine: Manifest, Domain-Service (Algorithmus aus radiquant4 selektiv migriert), Job, API, UI, Result+Provenance, Tests — je als eigener Feature-Branch + PR |
| **Akzeptanz** | Jede Engine E2E contract-/event-/testbar; PR grün gereviewt |
| **Verifikation** | CI grün pro PR |
| **Adressiert** | P-12 |

## W7 — Synergy, Harmonization, Reports

| Feld | Inhalt |
|---|---|
| **Ziel** | Cross-Module-Synergie + sichere Harmonisierung + Reports |
| **Primär** | Codex CLI + Devin (große Teile) |
| **Arbeit** | SynergyResult mit Confidence/Conflicts; Harmonization Plan mit Approval-Gate; Harmonization Job (Timer/Pause/Resume/Stop, Hardware-ACK/Fallback); Client Report + Therapist Appendix (Claim-Linter) |
| **Akzeptanz** | Therapist-Approval erzwungen; kein Claim-/Datenschutzbruch; Hardware-Fallback transparent |
| **Verifikation** | Safety-/Approval-/Claim-Tests grün |

## W8 — GDPR/Retention/Backup + Deployment-Baseline

| Feld | Inhalt |
|---|---|
| **Ziel** | Produktionsreife & rechtssicher |
| **Primär** | Codex CLI (Design: Cascade) |
| **Arbeit** | Export/Delete/Anonymize/Retention; verschlüsselte Backups + Restore-Runbook; Reverse Proxy/Ports/systemd/Docker; Prometheus/Grafana/SLOs |
| **Akzeptanz** | Restore-Test bestanden; Staging reproduzierbar; Security-Gates grün |
| **Verifikation** | Restore-Test + Security-Scan + Deployment-Smoke grün |
| **Adressiert** | P-11 |

## W9 — Innovation Labs (feature-flagged)

Siehe `03_INNOVATIONEN.md`. Erst nach stabilem Kern; alles abschaltbar und auditierbar.

---

## Wellen-Agenten-Matrix (Überblick)

| Welle | Cascade | Codex CLI | Devin |
|---|:--:|:--:|:--:|
| W0 Stabilisierung | Plan/Review | Ausführung | — |
| W1 CI | Design | Ausführung | — |
| W2 Radi144 E2E | Review | Ausführung | — |
| W3 Realtime | Review | Ausführung | — |
| W4 Frontend-Tests | Review | Ausführung | optional |
| W5 Admin/Ops | Review | Ausführung | — |
| W6 Engine 2–6 | Review | Fixes | **Primär** |
| W7 Synergy/Harmonize | Review | Ausführung | groß |
| W8 GDPR/Deploy | Design | Ausführung | — |
| W9 Labs | Design/Review | Ausführung | groß |
