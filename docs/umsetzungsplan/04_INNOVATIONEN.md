# 04 — Weiterführende professionelle Innovationen (Empfehlung)

> **Stand:** 2026-05-29 · Alle Innovationen: feature-flagged, auditierbar, abschaltbar, erst nach stabilem Kern (ab W9).

## A. Prozess-/Plattform-Innovationen (hoher Hebel, geringes Risiko)

| ID | Innovation | Nutzen |
|---|---|---|
| **I-01** | **Contract-Codegen-Pipeline** (OpenAPI → TS-Client automatisch) | Eliminiert Frontend-URL-Drift dauerhaft; CI-Gate auf Schema-Diff |
| **I-02** | **Golden-Path-E2E in CI** (Playwright MVP-Demo als Pflicht-Gate) | Verhindert Rückfall in Governance-ohne-Lieferung |
| **I-03** | **Agent-Ticket-Tracker** (leichtes Markdown-/Issue-System für Cascade↔Codex↔Devin) | Saubere Handoffs, weniger Reibung |
| **I-04** | **Provenance-First Result-Schema** (Modul, Version, Inputqualität, Fallback, Confidence verpflichtend) | Wissenschaftliche Nachvollziehbarkeit, Compliance |
| **I-05** | **Event-Replay-Lab** (anonymisierte Fixtures für reproduzierbare Realtime-Tests) | Stabile Realtime-Regression |

## B. Produkt-/Domänen-Innovationen (nach Engine-Kern)

| ID | Innovation | Nutzen | Flag |
|---|---|---|---|
| **I-06** | **HRV-gated Harmonization** | Adaptive, sichere Sitzungssteuerung | `feature.hrv` |
| **I-07** | **Quantum/Entropy-Optimierung** (reproduzierbar + Fallback) | Differenzierende Engine-Tiefe | `feature.quantum` |
| **I-08** | **LLM Therapist-Copilot** (PII-Redaction + Claim-Linter) | Effizienz, ohne Heilversprechen | `feature.llm_copilot` |
| **I-09** | **Adaptive Audio/Visual** (Chromotherapie + Circadian, WCAG-AAA) | Heilsame UX, A11y-konform | `feature.adaptive_ux` |
| **I-10** | **SynergyGraph** (Cross-Module-Beziehungsgraph mit Confidence) | Professionelle Analyse-Synthese | `feature.synergy_graph` |

## C. Betriebs-/Sicherheits-Innovationen

| ID | Innovation | Nutzen |
|---|---|---|
| **I-11** | **Route-Security-Matrix als CI-Gate** | Unklassifizierte Route = Build-Fail |
| **I-12** | **Automatischer Claim-Linter** (Wellbeing-Sprache erzwingen) | Compliance gegen Heilversprechen |
| **I-13** | **Tenant-Fuzzing-Tests** (automatische wrong-tenant Negativfälle) | Datenschutz-Härtung |
| **I-14** | **Kontextanker-Lint** (project.yml Größenlimit als CI-Gate) | Verhindert erneuten Anker-Bloat |
| **I-15** | **Decision-Gate-Limiter** (CI failt bei >1 Gate ohne Lieferartefakt) | Strukturelle Anti-Rekursions-Garantie |

## Priorisierung

```
Sofort sinnvoll (parallel zu W0–W4): I-01, I-02, I-04, I-11, I-12, I-14, I-15
Nach Engine-Kern (W6+):              I-05, I-10, I-13
Labs (W9):                            I-06, I-07, I-08, I-09
```

**Besonders empfohlen:** I-14 und I-15 — sie kodifizieren die Lehren aus der PI-Drift direkt als automatische Schutzregeln und verhindern einen Rückfall.
