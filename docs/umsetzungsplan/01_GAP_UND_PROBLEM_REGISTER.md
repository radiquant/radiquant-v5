# 01 — Gap- und Problem-Register (frische Codebasis-Prüfung)

> **Stand:** 2026-05-29 · read-only verifiziert · ergänzt die Ground-Zero-Analyse um Umsetzungs-relevante Lücken.

## A. Kritische Blocker (zuerst lösen)

| ID | Lücke/Problem | Beleg | Wirkung |
|---|---|---|---|
| **P-01** | **Keine Git-Historie** — v5 hat 0 Commits, alles untracked | `git rev-list --count HEAD` → fatal | Kein Rollback, kein Review-Diff, keine PR-Basis für Devin |
| **P-02** | **Decision-Gate-Rekursion** — 59+ Gates für `0008_module_projections.py`, Datei fehlt | `05_blocker_next_steps.md`, `make verify` | Lieferstillstand; blockiert Phase 12/13 |
| **P-03** | **Keine CI** — `.github` fehlt vollständig | `test -d .github` → NO | Anti-Drift-Gates laufen nur lokal/manuell; keine PR-Gates für Devin |
| **P-04** | **`verify` prüft nur Dateiexistenz** — kein echtes ruff/mypy/tsc/astro-build | `grep` in `verify_bootstrap.py` | Lint-/Typ-/Frontend-Fehler werden nicht gefangen |

## B. Hohe Priorität

| ID | Lücke/Problem | Beleg | Wirkung |
|---|---|---|---|
| **P-05** | **Keine Frontend-Tests** — kein vitest/playwright/`*.test`/`*.spec` | `find apps/web-astro` leer | MVP-Gate 9 (Frontend Contract/A11y/Realtime-Tests) unerfüllbar |
| **P-06** | **Skript-/Script-Inflation** — 104 npm-Scripts, 77 Decision-Check-Skripte, 102 py-Skripte | `package.json`, `ls scripts/` | Wartungslast, Navigationschaos, langsamer `verify` |
| **P-07** | **Kontextanker-Bloat** — `docs/pi/project.yml` 4.898 Zeilen/262 KB | `wc -l` | Agenten laden riesigen Anker; Kontextkosten, Drift-Risiko |
| **P-08** | **Test-Aussagekraft** — 69/98 Testdateien prüfen Governance statt Funktion | `ls tests/` | Grüne Suite ohne Feature-Beweis |

## C. Mittlere Priorität / Reife

| ID | Lücke/Problem | Wirkung |
|---|---|---|
| **P-09** | Phase 12 Radi144 nicht end-to-end nutzwert-bewiesen (kein realer Result→UI-Flow demonstriert) | MVP-Demo fehlt |
| **P-10** | Realtime (SSE/Fallback) nur als Gate, keine echte Reconnect-/Replay-Demo | Engine-Fortschritt nicht real sichtbar |
| **P-11** | Keine Deployment-/Ops-Baseline (Proxy/Ports/systemd/Monitoring) | Kein Staging-Pfad |
| **P-12** | Keine selektive Algorithmus-Migration aus radiquant4 begonnen | Engine-Logik noch nicht portiert |

## D. Konsolidierungspotenzial (Aufräumen statt Wegwerfen)

| Bereich | Empfehlung |
|---|---|
| 59+ Decision-Gate-Docs | Zu **einer** ADR „Materialized Projection" zusammenführen, Rest archivieren |
| 77 Decision-Check-Skripte | Durch 1 echten Migrations-/ORM-/Write-Service-Test ersetzen |
| 104 npm-Scripts | Auf sinnvolle Kernscripts reduzieren (dev/build/test/lint/typecheck/verify) |
| `project.yml` | Auf schlanken Zustandsanker < 5 KB reduzieren |

## E. Priorisierte Reihenfolge der Lösung

```
P-01 (Git) → P-02 (Schleife stoppen) → P-04 (verify härten) → P-03 (CI)
→ P-06/P-07 (Konsolidierung) → P-05 (Frontend-Tests) → P-09/P-10 (Radi144 E2E + Realtime)
→ P-11 (Deployment) → P-12 (Migration) → Innovationen
```
