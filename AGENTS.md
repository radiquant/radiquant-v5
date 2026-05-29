# AGENTS.md — radiquant-v5 Multi-Agent Operating Contract

> **Gültig ab:** 2026-05-29 · **Status:** VERBINDLICH für alle Agenten (Cascade, Codex CLI, Devin)
> **Projekt:** `/opt/radiquant-v5` (kontrollierter Ground-Zero-Rebuild)
> **Referenz/SSOT-Doku:** `/opt/radiquant4/docs/restart-radiquant-v5/`

Jeder Agent liest diese Datei als erste Amtshandlung. Codex CLI und Devin lesen `AGENTS.md` automatisch als Projektinstruktion.

---

## 1. Rollenmodell (drei Agenten, klare Grenzen)

| Agent | Rolle | Domäne | Darf | Darf NICHT |
|---|---|---|---|---|
| **Cascade (Windsurf IDE)** | Architekt, Kontext, Entscheidungen | Planung, Reviews, Contracts, ADRs, Gate-Definition | Pläne/ADRs schreiben, Contracts entwerfen, Code reviewen, kleine gezielte Edits | Lange autonome Code-Massenarbeit ohne Review |
| **Codex CLI (Terminal)** | Implementierer | Konkrete Codeänderungen im Repo | Features/Tests/Migrationen lokal implementieren, `make verify` ausführen, committen | Architektur-/Scope-Entscheidungen eigenmächtig ändern |
| **Devin (Cloud)** | Autonomer Langläufer | Größere, gut spezifizierte Tickets mit Tests + PR | Mehrstündige Tasks, Test-Suiten, PR-Erstellung | Arbeiten an unklaren/unspezifizierten Tickets ohne Akzeptanzkriterien |

**Grundprinzip:** Cascade entscheidet *was* und *warum*, Codex CLI macht das *wie* lokal, Devin übernimmt *breite, spezifizierte* Arbeit autonom.

---

## 2. Handoff-Protokoll

Jede Aufgabe läuft als **Ticket** mit diesem Minimalvertrag:

```
TICKET-ID: <Wxx-NN>
ZIEL: <1-2 Sätze>
AGENT: cascade | codex-cli | devin
INPUTS: <Dateien/Contracts/ADRs>
AKZEPTANZ: <prüfbare Kriterien>
VERIFIKATION: make verify && pytest && (npm run typecheck)
SCOPE-GRENZE: <was NICHT angefasst wird>
COMMIT: conventional commit, nach grünem verify
```

Handoff-Regeln:

| Übergang | Regel |
|---|---|
| Cascade → Codex CLI | Cascade liefert Ticket + Contract; Codex CLI implementiert nur innerhalb der Scope-Grenze |
| Cascade → Devin | Nur Tickets mit vollständigen Akzeptanzkriterien + Testerwartung |
| Codex CLI/Devin → Cascade | Bei Contract-/Architektur-/Scope-Fragen zurück an Cascade, keine Eigenentscheidung |

---

## 3. Harte Anti-Drift-Invarianten (alle Agenten)

1. **Keine unklassifizierte Route** — jede Route public/auth/tenant/admin/internal.
2. **Keine Frontend-URL ohne Contract** — nur zentraler API-Client.
3. **Kein Workflow-Step außerhalb Manifest v2.**
4. **Keine Client-Roh-/Debugdaten.**
5. **Kein sensibler Klartext in Produktion.**
6. **Kein Realtime ohne Fallback.**
7. **Keine Innovation ohne Feature-Flag.**
8. **Keine medizinischen Heilversprechen.**

---

## 4. Anti-Rekursions-Regel (kritisch, Lehre aus PI-Drift)

| Regel | Bedeutung |
|---|---|
| **Ein Gate pro lieferbarem Artefakt** | Ein Decision-Gate darf KEINE weiteren „prepare-to-decide"-Gates erzeugen. |
| **Liefer-Definition** | „Fertig" = Code + Migration + Test, der **Funktion** prüft — nicht die Abwesenheit einer Datei. |
| **Decision-only-Verbot** | Tests, die nur „Datei bleibt absent" prüfen, zählen NICHT als Fortschritt. |
| **Max. ein ADR pro Feature** | Statt Gate-Kaskaden: ein Architecture Decision Record + reale Umsetzung. |

---

## 5. Verifikation & Commit-Disziplin

| Pflicht | Befehl |
|---|---|
| Backend | `python3 -m pytest -q` |
| Bootstrap-Gates | `make verify` |
| Lint | `ruff check .` |
| Typecheck Backend | `mypy apps/api` |
| Typecheck Frontend | `npm run typecheck` (sobald verdrahtet) |
| Commit | nach grünem Verify, conventional commits, kleine Einheiten |

**Git ist Pflicht:** Jede abgeschlossene Einheit wird committet. Kein Arbeiten ohne initialisierte Git-Historie.

---

## 6. Kontext-Hygiene

- `docs/pi/project.yml` bleibt **schlanker Zustandsanker** (Zielgröße < 5 KB). Detailzustand gehört in datierte `docs/project-overview/*`-Statusdocs.
- Keine Append-Logs in Kontextanker.
- Architekturänderungen aktualisieren das zugehörige ADR, nicht hundert Einzeldateien.

---

## 7b. Verbindlicher Arbeitszyklus (Cascade ↔ User ↔ Codex CLI) — FIXIERT

Dieser Zyklus ist bis zur vollständigen Projekt-Finalisierung der verbindliche Standardablauf:

```
1. Cascade bereitet den nächsten Schritt im EXAKTEN Wortlaut für Codex CLI vor
   (copy-paste-fertiges Prompt/Ticket inkl. Akzeptanz + Verifikationsbefehlen).
2. User führt diesen Wortlaut in Codex CLI aus.
3. User gibt Cascade die finale Rückmeldung (Output/Logs/Diff/Fehler).
4. Cascade prüft die Funktionalität (Verifikation, Akzeptanzkriterien, Regressionen).
5. Bei grün: nächster Schritt. Bei rot: Cascade liefert exakten Korrektur-Wortlaut.
   → Wiederholen bis Welle/Projekt abgeschlossen.
```

| Regel | Bedeutung |
|---|---|
| **Exakter Wortlaut** | Cascade liefert Codex-CLI-Schritte immer copy-paste-fertig, nicht paraphrasiert. |
| **Ein Schritt zur Zeit** | Nur der jeweils nächste, klar abgegrenzte Schritt; kein Vorgreifen. |
| **User ist Ausführer** | Cascade führt Codex-CLI-Schritte NICHT selbst aus; der User führt aus und meldet zurück. |
| **Cascade verifiziert** | Cascade bewertet nach jeder Rückmeldung Funktionalität + Akzeptanz, bevor es weitergeht. |
| **Lückenlos bis Finalisierung** | Dieser Loop gilt für alle Wellen W0–W9 bis zum Projektabschluss. |

## 7. Verweise

- Umsetzungsplan: `/opt/radiquant4/docs/restart-radiquant-v5/umsetzungsplan-v5-2026-05-29/`
- Ground-Zero-Analyse: `/opt/radiquant4/docs/analysis/ground-zero-v5-vs-v4-2026-05-29/`
- Optimale Schrittfolge: `/opt/radiquant4/docs/restart-radiquant-v5/08_OPTIMAL_REBUILD_SEQUENCE.md`
- MVP-Gates: `/opt/radiquant4/docs/restart-radiquant-v5/07_MVP_GATES_AND_ACCEPTANCE.md`
