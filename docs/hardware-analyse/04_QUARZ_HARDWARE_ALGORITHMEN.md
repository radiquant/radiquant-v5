# 04 — Quarz-Kristall: Hardware-Referenz vs. Algorithmische Implementierung

> **Quelle:** `/opt/radiquant4/apps/api/app/services/hardware/kozyrev_driver.py` (Zeilen 276–373)
> **Status in v5:** ❌ Nicht vorhanden.
> **WICHTIG:** Es gibt in dieser Codebasis **keine echte Quarz-Kristall-Hardware**. Die Quarz-Signatur ist vollständig algorithmisch (software-emuliert).

---

## 1. Was ist die "Quarz-Signatur"?

Die Quarz-Signatur (`_last_quartz_signature`, `_measure_quartz_signature`) ist eine **algorithmische Messung des CPU-Clock-Jitters**, modelliert als würde eine Quarz-Kristall-Schwingung (32.768 kHz — Standard für Real-Time-Clock-Quarze) vermessen.

**Keine physische Hardware-Anforderung.** Alles läuft rein auf der Host-CPU.

---

## 2. `_measure_quartz_signature` (kozyrev_driver.py, Zeile 276)

### Messmethode

```python
async def _measure_quartz_signature(self, sample_count: int = 48) -> tuple[float, float]:
    """Misst eine algorithmische Quarz-Kohärenz aus Clock-Drift und Phasenfehlern."""
```

**Ablauf:**
1. Sammelt `sample_count` (Standard: 48) CPU-Timing-Proben via `time.perf_counter_ns()`
2. Misst die Standardabweichung der Lücken zwischen den Proben (Clock-Jitter)
3. **Kohärenz-Berechnung:** Ideal wäre ein perfekt periodischer Takt → kleiner Jitter = hohe Kohärenz

    ```python
    coherence = max(0.0, min(100.0, (1.0 - rel_jitter) * 100.0))
    ```

4. **Phasen-Akkumulation:** Modelliert die kumulative Phasenabweichung vom idealen 32.768 kHz Takt
    - Nominale Periode: `1.0 / 32768.0` Sekunden
    - Jeder gemessene Intervall weicht von diesem Nominal ab → akkumulierter Phasenfehler

---

## 3. `_apply_quartz_signature` (Zeile 316)

Moduliert den Basisvektor mit einer algorithmischen Quarz-Schwingung:

```python
quartz_wave = (
    np.sin((2π · 32768 · idx) + phase)              # 32.768 kHz Grundton
    + 0.5 * np.sin((2π · 10 · φ · idx) + (phase/φ)) # Goldener Schnitt Oberton
)
amplitude = 0.04 + (quartz_coherence / 100.0) * 0.08  # 4–12% Amplitude
```

- `32768 Hz` = Quarz-Referenzfrequenz (typisch für RTC-Quarze)
- `φ = 1.61803398875` = Goldener Schnitt als Frequenzverhältnis
- **Einfluss auf finales Ergebnis:** Amplituden-Modulation ±4–12% des Basis-Signals

---

## 4. Gewichtung in der Entropie-Pipeline

Die Quarz-Signatur fließt mit **20% Gewicht** in die finale Entropie ein:

| Pfad | Formel |
|---|---|
| Ohne GPU | `entropy = cpu_wavelet * 0.80 + quartz * 0.20` |
| Mit GPU | `entropy = cpu_wavelet * 0.35 + gpu_wavelet * 0.45 + quartz * 0.20` |

**Rückgabewert:** `{"quartz": float}` im `read_entropy()` Ergebnis-Dict.

---

## 5. Warum "Quarz-Signatur" — Konzeptioneller Hintergrund

Quarz-Kristalle in realen Radionik-Geräten sollen gemäß radionischer Theorie:
- Kohärenz in Schwingungsfeldern erzeugen
- Als Energie-Stabilisatoren wirken
- Die Trägerfrequenz "verfeinern"

Die Software-Implementation modelliert diese Eigenschaft durch Messung der **Takt-Kohärenz** des Host-Systems als Proxy. Das Ergebnis ist deterministisch reproduzierbar für dasselbe System unter gleicher Last.

---

## 6. Gibt es keine echte Quarz-Hardware?

In der gesamten Codebasis (`/opt/radiquant4`) gibt es:
- ✅ Algorithmische Quarz-Signatur (kozyrev_driver.py) — vollständig
- ✅ `HidSource` (entropy_sources.py) — generischer HID-Sensor (VID 0x0E50, PID 0x0002) als optionale physische Entropie-Quelle
- ❌ Kein dedizieter Quarz-Hardware-Treiber
- ❌ Kein USB-Quarz-Interface
- ❌ Keine direkten Hardware-Quarze angeschlossen

Die einzige "physische Nähe" zu Quarz-Hardware wäre das Quarz im Host-System-CPU-Takt, dessen Jitter algorithmisch gemessen wird.

---

## 7. Betroffene Dateien (Übersicht)

| Datei | Relevanz |
|---|---|
| `apps/api/app/services/hardware/kozyrev_driver.py` | **Haupt-Implementierung** — `_last_quartz_signature`, `_measure_quartz_signature`, `_apply_quartz_signature`, `_build_reality_signal` |
| `apps/api/app/services/hardware/spooky2_driver.py` | Nutzt `kozyrev_entropy["quartz"]` im Virtual-ACK (Zeile 738) |
| `apps/api/app/routes/kozyrev.py` | Exposes `kozyrev_entropy` + `kozyrev_combined` via API |
