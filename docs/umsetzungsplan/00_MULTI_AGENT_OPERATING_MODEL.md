# 00 — Multi-Agent Operating Model (Cascade + Codex CLI + Devin)

> **Stand:** 2026-05-29 · Teil des v5-Umsetzungsplans · SSOT für die Agenten-Arbeitsteilung.

## Leitidee

„Nahtlos" bedeutet hier **gut integrierbar**, nicht ein einziger einheitlicher Arbeitsfluss. Die drei Agenten bleiben getrennte Komponenten mit unterschiedlichen Oberflächen und Session-Modellen. Der Plan minimiert Kontextwechsel-Reibung durch **klare Rollen, ein gemeinsames Ticket-Format und einen einzigen Verifikationsstandard**.

## Rollenaufteilung (empfohlen)

| Agent | Primärrolle | Typische Aufgaben | Session-Modell |
|---|---|---|---|
| **Windsurf/Cascade** | Kontext, Architektur, Entscheidungen | Pläne, ADRs, Contract-Entwurf, Code-Review, kleine präzise Edits, Verifikations-Orchestrierung | interaktiv, IDE-nah |
| **Codex CLI** | Konkrete Codeänderungen im Terminal | Migrationen, Services, Routen, Backend-/Frontend-Implementierung, lokale Tests/Commits | terminal-lokal, kurzzyklisch |
| **Devin** | Längere autonome Aufgaben | Breite Engine-Rollouts, Test-Suiten, Refactors, PR-Erstellung | cloud-autonom, langläufig |

## Warum diese Trennung

- **Cascade** hat den besten Repo-/Kontextüberblick und eignet sich für Entscheidungen und Reviews.
- **Codex CLI** ist ideal für schnelle, eng begrenzte Codeänderungen direkt am lokalen Repo mit sofortigem `make verify`.
- **Devin** trägt breite, gut spezifizierte Arbeit (z.B. Engine 2–6 nach Muster) autonom inkl. PR.

## Gemeinsamer Ticket-Vertrag

Alle drei Agenten arbeiten gegen dasselbe Ticket-Format (siehe `AGENTS.md` §2). Cascade erzeugt Tickets; Codex CLI/Devin führen aus; Rückfragen zu Architektur/Scope gehen an Cascade zurück.

## Reibungsminimierung (Workflow-Disziplin)

| Reibungsquelle | Gegenmaßnahme |
|---|---|
| Zu häufiges Hin-/Herspringen | Pro Welle EIN Primäragent; andere nur bei Bedarf |
| Divergierende Verifikation | Einheitlich `make verify` + `pytest` + `typecheck` überall |
| Kontextverlust zwischen Agenten | Ticket + ADR als schriftlicher Übergabezustand |
| Merge-Konflikte | Devin arbeitet auf Feature-Branches mit PR; Codex CLI committet kleinteilig |
| Scope-Drift | Scope-Grenze ist Pflichtfeld jedes Tickets |

## Empfohlene Zuständigkeit pro Wellentyp

| Wellentyp | Primär | Sekundär |
|---|---|---|
| Stabilisierung/Cleanup (W0) | Cascade (Plan) + Codex CLI (Ausführung) | — |
| Contract-/Architekturentscheidung | Cascade | — |
| Vertikale Feature-Implementierung | Codex CLI | Cascade (Review) |
| Breiter Engine-Rollout 2–6 | Devin | Cascade (Review), Codex CLI (Fixes) |
| CI/Tooling-Setup | Codex CLI | Cascade (Design) |
| Review/Verifikation/Merge-Gate | Cascade | — |

## Fixierter Arbeitszyklus bis zur Finalisierung

Verbindlich vereinbart (2026-05-29): Der primäre Ausführungsmodus ist der **Cascade-prepares / User-executes / Cascade-verifies**-Loop.

| Schritt | Verantwortlich | Inhalt |
|---:|---|---|
| 1 | **Cascade** | Bereitet den nächsten Codex-CLI-Schritt im **exakten, copy-paste-fertigen Wortlaut** vor (Ticket + Befehle + Akzeptanz + Verifikation). |
| 2 | **User** | Führt den Wortlaut in Codex CLI aus. |
| 3 | **User** | Gibt Cascade die finale Rückmeldung (Output, Logs, Diff, Fehler). |
| 4 | **Cascade** | Prüft Funktionalität, Akzeptanzkriterien und Regressionen. |
| 5 | **Cascade** | Bei grün → nächster Schritt; bei rot → exakter Korrektur-Wortlaut. |

Dieser Loop wiederholt sich pro Schritt über alle Wellen **W0–W9 bis zum vollständigen Projektabschluss**. Devin wird innerhalb dieses Modells nur für breite, vom User beauftragte autonome Epics herangezogen; die Verifikation der Ergebnisse bleibt bei Cascade.

## Grenzen (ehrlich)

- Es bleibt ein **Multi-Tool-Workflow**, kein monolithischer Agent. Übergänge sind manuell.
- Devin-PRs müssen von Cascade reviewt werden, bevor sie in `main` gehen.
- Codex CLI und Devin teilen sich das Repo — Branch-Disziplin ist Pflicht, sonst Konflikte.
