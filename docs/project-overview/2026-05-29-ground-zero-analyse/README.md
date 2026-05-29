# Ground-Zero-Analyse v5 vs. v4 — Kurzfassung (2026-05-29)

> **Vollständige Analyse (SSOT):** `/opt/radiquant4/docs/analysis/ground-zero-v5-vs-v4-2026-05-29/00_GROUND_ZERO_ANALYSE.md`  
> **Belege/Kennzahlen:** `/opt/radiquant4/docs/analysis/ground-zero-v5-vs-v4-2026-05-29/01_EVIDENZ_UND_KENNZAHLEN.md`  
> **Modus:** reine Analyse, keine Code-Änderungen · **Agent bis dato:** PI

## Kernurteil

- **Plan = akkurat & nahezu lückenlos.** `08_OPTIMAL_REBUILD_SEQUENCE.md` + Phasen 0–26 sind diszipliniert und MVP-tauglich.
- **Umsetzung = methodisch fehlerhaft & lieferblockiert.** Über-Granularisierung in Decision-Gates statt realer Lieferung.

## Wichtigste Befunde

| ID | Befund | Schwere |
|---|---|---|
| GZ-01 | 59+ rekursive Decision-Gates für **eine** Datei `0008_module_projections.py`; Datei fehlt weiterhin | 🔴 |
| GZ-02 | v5 hat **0 Git-Commits**, alles untracked — kein Rollback/History | 🔴 |
| GZ-03 | `docs/pi/project.yml` = 4.898 Zeilen/262 KB (v4: ~1,9 KB) | 🟠 |
| GZ-04 | Phase 12/13 real 0 % materialisierte Projection (Selbstbericht „~60 %") | 🟠 |
| GZ-05 | 69/98 Testdateien prüfen Governance-Zustände, nicht Funktion | 🟠 |

## Realer Stand (verifiziert)

- Phasen 0–11 solide real umgesetzt; `make verify`/`pytest` grün.
- 20 Routen klassifiziert, 15 OpenAPI-Pfade, Migrationen `0001`–`0007` real, `0008` fehlt.
- Fundament deutlich besser als radiquant4 (keine Drift), aber aktuell **lieferblockiert**.

## Empfohlene Sofortmaßnahmen

1. **Git-Baseline committen** (Historie/Rollback herstellen).
2. **Decision-Schleife stoppen:** eine „Unlock & Implement"-Entscheidung — `0008` real anlegen oder Phase 13 zurückstellen und Phase 12 vertikal abschließen.
3. **Decision-Artefakte konsolidieren** zu 1 ADR + echten Funktionstests.
4. **Kontextanker entschlacken** auf schlanke Zielgröße.
5. **Echte Radi144-MVP-Demo** end-to-end grün beweisen.

> Details, Plantreue-Matrix (Phasen 0–26) und vollständiges Remediation-Kapitel siehe SSOT-Hauptdokument in radiquant4.
