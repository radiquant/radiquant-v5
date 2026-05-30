# 03 — Codex CLI Integration (konkrete Einrichtung)

> **Stand:** 2026-05-29 · Ziel: Codex CLI als Terminal-Implementierer sauber in den v5-Workflow einbinden.

## 1. Voraussetzungen

| Punkt | Empfehlung |
|---|---|
| Account | Dein bestehender Codex-CLI-Account |
| Arbeitsverzeichnis | immer `/opt/radiquant-v5` (eigener Git-Root) |
| Projektinstruktion | `AGENTS.md` im v5-Root (bereits erstellt) — Codex CLI liest dies automatisch |
| Git | initiale Baseline muss existieren (W0), sonst keine sauberen Diffs/PRs |

## 2. Rolle von Codex CLI (eng begrenzt)

Codex CLI ist der **Implementierer für konkrete, eng abgegrenzte Codeänderungen**:

- Migrationen, Services, Routen, Schemas, Frontend-Islands, Tests.
- Führt nach jeder Änderung `make verify` + `pytest` aus.
- Committet kleinteilig mit conventional commits.
- Eskaliert Architektur-/Scope-Fragen zurück an Cascade.

Codex CLI trifft **keine** Architektur-/Scope-Entscheidungen eigenmächtig.

## 3. Empfohlene Guardrails

| Guardrail | Umsetzung |
|---|---|
| Scope-Grenze | Jedes Ticket nennt explizit, was NICHT angefasst wird |
| Verifikationspflicht | Kein Commit ohne grünes `make verify` + `pytest` |
| Anti-Rekursion | Keine neuen Decision-Gate-Skripte; ein ADR + reale Umsetzung |
| Branch-Disziplin | Feature-Branch pro Ticket, klein halten |
| Secret-Schutz | Niemals echte Secrets committen; nur `.env.example` |

## 4. Standard-Ticket für Codex CLI (Vorlage)

```
TICKET-ID: W2-01
ZIEL: Reale module_projections Migration + ORM + Write Service implementieren
AGENT: codex-cli
INPUTS:
  - ADR docs/architecture/ADR_MATERIALIZED_PROJECTION.md
  - apps/api/app/models/, apps/api/alembic/versions/
AKZEPTANZ:
  - 0008_module_projections.py mit up/down, getestet
  - ORM ModuleProjection mit tenant_id + Constraints
  - Projection Write Service mit Idempotenz + Hash/Role/Retention
  - Funktionstests (KEIN "Datei bleibt absent"-Test)
  - Tenant-Isolation-Test grün
VERIFIKATION: make verify && pytest && ruff check . && mypy apps/api
SCOPE-GRENZE: keine neue Runtime-Route, keine GPU/CUDA, kein Realtime
COMMIT: feat(radi144): materialize module projections (migration+orm+writer)
```

## 5. Typischer Codex-CLI-Arbeitszyklus

```
1. Cascade erstellt Ticket + ADR
2. Codex CLI: git checkout -b feat/w2-01-module-projections
3. Codex CLI implementiert gemäß Akzeptanz
4. Codex CLI: make verify && pytest && ruff check . && mypy apps/api
5. Codex CLI: git commit (conventional) → push
6. Cascade reviewt Diff → Merge (oder Rückfrage)
```

## 6. Aufgabenteilung Codex CLI vs. Devin

| Kriterium | Codex CLI | Devin |
|---|---|---|
| Dauer | kurz, interaktiv | lang, autonom |
| Umfang | 1 eng begrenztes Ticket | breite, gut spezifizierte Epics |
| Beispiel | „Implementiere W2-01" | „Rolle Engine 2–6 nach Radi144-Muster aus, je PR" |
| Output | lokale Commits/Branch | PRs mit Tests |

## 7. Was Cascade beisteuert (damit Codex CLI effizient ist)

- Klare Tickets mit prüfbaren Akzeptanzkriterien.
- ADRs statt Gate-Kaskaden.
- Reviews der Codex-CLI-Diffs.
- Pflege des schlanken Kontextankers `docs/pi/project.yml`.
