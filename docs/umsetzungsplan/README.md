# Umsetzungsplan radiquant-v5 (2026-05-29)

Lückenloser, agentenzugeordneter Umsetzungsplan für den optimalen, contract-first Weiterbau von `/opt/radiquant-v5` mit integriertem Multi-Agent-Workflow (Windsurf/Cascade + Codex CLI + Devin).

## Dokumente (Lesereihenfolge)

1. **[Operating Model]** `00_MULTI_AGENT_OPERATING_MODEL.md` — Rollen, Handoffs, Reibungsminimierung
2. **[Gap-Register]** `01_GAP_UND_PROBLEM_REGISTER.md` — frische Codebasis-Lücken P-01…P-12
3. **[Wellenplan]** `02_UMSETZUNGSPLAN_WELLEN.md` — W0…W9, je Ziel/Agent/Akzeptanz/Verifikation
4. **[Codex CLI]** `03_CODEX_CLI_INTEGRATION.md` — konkrete Einrichtung, Ticket-Vorlage, Arbeitszyklus
5. **[Innovationen]** `04_INNOVATIONEN.md` — I-01…I-15, feature-flagged
6. **[Fortschritts-Log]** `05_FORTSCHRITT_LOG.md` — **lebendes Status-Log**: jeder Schritt/Ticket mit Status, Commit, Verifikationsbeleg
7. **[Vollplan W3–W9]** `06_VOLLPLAN_W3_W9_DETAILLIERT.md` — **maximale Detaillierung**: G-01 + W3–W9 mit Agent, Scope, Codex-Prompts, Akzeptanzkriterien, Verifikation

## Aktueller Stand

Der jeweils aktuelle Umsetzungsstand (welche Welle/welches Ticket erledigt, verifiziert, offen) steht **immer** in `05_FORTSCHRITT_LOG.md`. Dieses Log ist die entwicklerseitige Single Source of Truth für den Projektfortschritt innerhalb von `/opt/radiquant-v5`.

## Begleitartefakte

- **Agent-Vertrag im Zielrepo:** `/opt/radiquant-v5/AGENTS.md` (von Cascade, Codex CLI, Devin gelesen)
- **Lebender Systemzustand:** `/opt/radiquant-v5/SYSTEM_STATE.md`
- **Ground-Zero-Analyse (Ursprung in radiquant4):** `/opt/radiquant4/docs/analysis/ground-zero-v5-vs-v4-2026-05-29/` — Spiegelkurzfassung unter `/opt/radiquant-v5/docs/project-overview/2026-05-29-ground-zero-analyse/`

## Kern-Reihenfolge in einem Satz

`W0 Git+Stabilisierung → W1 CI → W2 Radi144 echtes E2E → W3 Realtime → W4 Frontend-Tests+MVP-Demo → W5 Admin/Ops → W6 Engine 2–6 (Devin) → W7 Synergy/Harmonize → W8 GDPR/Deploy → W9 Labs.`

---

## Wie realistisch ist der angedachte Multi-Agent-Plan?

**Urteil: Realistisch und gut umsetzbar — mit einer ehrlichen Einschränkung.**

| Aspekt | Bewertung |
|---|---|
| **Rollenidee (Cascade=Kontext/Architektur, Codex CLI=Code, Devin=autonom+PR)** | ✅ Sehr realistisch. Genau die Stärken der drei Werkzeuge; bewährte Trennung. |
| **„Nahtlos" als ein einziger Fluss** | ⚠️ Nicht realistisch. Es bleiben drei getrennte Komponenten mit eigenen Oberflächen/Session-Modellen. „Gut integrierbar" ja, „nahtlos verschmolzen" nein. |
| **Reibung durch Tool-Wechsel** | ⚠️ Real, aber **beherrschbar**: gemeinsames Ticket-Format, ein Verifikationsstandard, Branch-Disziplin und klare Primäragenten pro Welle reduzieren das Hin-/Herspringen deutlich. |
| **Codex CLI als Implementierer** | ✅ Realistisch, sobald die Git-Baseline (W0) existiert — vorher keine sauberen Diffs/Commits. |
| **Devin für Engine-Rollout 2–6** | ✅ Realistisch, **aber** Voraussetzung: stabiler Radi144-Musterpfad (W2) + CI (W1) + klare Tickets. Sonst produziert Devin breit auf wackliger Basis. |
| **Voraussetzungen** | 🔴 Kritisch: Erst die Blocker P-01 (Git), P-02 (Decision-Schleife), P-03 (CI), P-04 (echtes verify) lösen. Ohne diese ist der Multi-Agent-Plan nicht tragfähig. |

**Fazit:** Dein Plan ist professionell und tragfähig. Erfolgsentscheidend ist die Reihenfolge: **erst W0/W1 (Git, Schleife stoppen, CI, verify härten)**, dann skaliert der Multi-Agent-Ansatz sehr gut. Erwarte einen integrierten, nicht einen monolithischen Arbeitsfluss — die verbleibende Reibung ist ein Workflow-Thema, kein technischer Blocker.
