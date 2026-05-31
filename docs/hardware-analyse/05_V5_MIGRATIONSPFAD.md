# 05 — v5 Migrationspfad: Hardware-Stack

> **Stand:** v5 hat aktuell KEINE Hardware-Integration.
> **Ziel:** Schrittweise Migration aus radiquant4 in die v5-Architektur mit Feature-Flags.

---

## 1. Ist-Zustand in radiquant-v5

```
/opt/radiquant-v5/apps/api/app/
    ├── services/           ← KEIN hardware/ Unterordner
    └── routes/             ← KEIN kozyrev.py / hardware.py
```

radiquant-v5 hat **keine Hardware-Abstraktion, keinen HALManager, keinen EntropyPool**. Alle Algorithmen (Radi144, RadiWorks, RadiBlohm, RadiThoms, RadiMorphic, RadiCopen) laufen in v5 ohne Hardware-Entropie — sie nutzen deterministischen Seed oder Python-`random`.

---

## 2. Migrationsstrategie: Feature-Flag-basiert

### Empfohlene Reihenfolge (nach W3)

| Wave | Hardware-Komponente | Abhängigkeit |
|---|---|---|
| **W4** | `CPUGPUEntropyDriver` — CPU-RDRAND/Timing-Jitter | Nur numpy + optional cupy |
| **W5** | `EntropyPoolService` + `seed_generator.py` TRNG-Kaskade | W4 abgeschlossen |
| **W6** | `KozyrevEntropyDriver` (CPU p-adische Wavelets) | W5 abgeschlossen |
| **W7** | `KozyrevEntropyDriver` (GPU CUDA) | W6 + CuPy verfügbar |
| **W8** | `Spooky2Driver` (Virtual Mode first, dann Real) | W5 abgeschlossen |
| **W9** | `QrngSource` / `pyqrng` / `HidSource` | W8 abgeschlossen |

### Feature-Flag-Schema (empfohlen)

Alle Hardware-Features hinter Environment-Variablen:

```python
HARDWARE_ENTROPY_ENABLED = os.getenv("RQ5_HARDWARE_ENTROPY", "false").lower() == "true"
KOZYREV_GPU_ENABLED = os.getenv("RQ5_KOZYREV_GPU", "false").lower() == "true"
SPOOKY2_ENABLED = os.getenv("RQ5_SPOOKY2", "false").lower() == "true"
QRNG_ENABLED = os.getenv("RQ5_QRNG", "false").lower() == "true"
```

---

## 3. Minimale Migration für W3 (sofort umsetzbar)

Für W3 ist **keine Hardware-Migration erforderlich**. W3 betrifft SSE/Realtime-Routen.

Das einzige Hardware-relevante Element in W3 ist der **`entropy_source_check`-Substep** im RadiWorks-Workflow-Manifest. Dieser Substep benötigt in v5 keinen echten Entropy-Driver — ein Stub genügt:

```python
# W3: Entropy-Substep-Stub für RadiWorks
async def entropy_source_check() -> dict:
    return {"source": "os_urandom", "available": True, "entropy_bits": 256}
```

---

## 4. Abhängigkeitsmatrix

| Python-Paket | Hardware-Komponente | pip-install |
|---|---|---|
| `numpy` | KozyrevEntropyDriver (CPU), TorsionFieldGenerator | `numpy>=1.24` |
| `scipy` | KozyrevEntropyDriver (FFT/Spectral) | `scipy>=1.10` |
| `cupy-cuda12x` | KozyrevEntropyDriver (GPU), GpuSource | `cupy-cuda12x>=12.0` — optional |
| `psutil` | EntropyCollector, CPUGPUEntropyDriver | `psutil>=5.9` |
| `pyserial` | Spooky2Driver (Serial Transport) | `pyserial>=3.5` — optional |
| `hid` (hidapi) | Spooky2Driver (HID Fallback), HidSource | `hidapi>=0.14` — optional |
| `pyqrng` | QrngSource (Quantis USB) | `pyqrng>=0.1` — optional, extern |
| `redis` | EntropyPoolService (Session-Isolation Lock) | `redis>=4.5` |

---

## 5. Risiken bei Migration

| Risiko | Beschreibung | Mitigation |
|---|---|---|
| **R-HW-01** | CUDA nicht verfügbar in Prod-Container | Feature-Flag `RQ5_KOZYREV_GPU=false` als Default |
| **R-HW-02** | Spooky2 Protokoll proprietär | Virtual Mode als Default; echte Hardware optional |
| **R-HW-03** | pyqrng nicht öffentlich verfügbar | os.urandom als Fallback immer vorhanden |
| **R-HW-04** | EntropyPool benötigt Redis-Lease | Redis muss für Session-Isolation konfiguriert sein |
| **R-HW-05** | Quarz-Signatur CPU-lastintensiv (48 Proben) | Sample-Count konfigurierbar, Default reduzieren |
| **R-HW-06** | HALManager Singleton — nicht thread-safe bei mehreren Workers | Lazy-Init mit asyncio.Lock absichern |

---

## 6. Empfohlener Zielzustand v5 (Hardware-Ordner)

```
apps/api/app/services/hardware/
    ├── __init__.py
    ├── base_driver.py              ← aus radiquant4 portieren
    ├── cpu_gpu_entropy_driver.py   ← aus radiquant4 portieren
    ├── entropy_pool.py             ← aus radiquant4 portieren (+ v5-Tenant-Isolation)
    ├── entropy_sources.py          ← aus Morphic_Engine_V2 portieren
    ├── kozyrev_driver.py           ← aus radiquant4 portieren
    ├── kozyrev_diode_driver.py     ← aus radiquant4 portieren (optional)
    ├── torsion_field_generator.py  ← aus radiquant4 portieren
    ├── seed_generator.py           ← aus radiquant4 portieren
    ├── spooky2_driver.py           ← aus radiquant4 portieren
    ├── preset_mapping_service.py   ← aus radiquant4 portieren
    ├── hal_manager.py              ← aus radiquant4 portieren
    ├── mock_driver.py              ← aus radiquant4 portieren
    ├── registry.py                 ← aus radiquant4 portieren
    └── hardware_state.py           ← aus radiquant4 portieren
```

Zusätzlich benötigt:
- `apps/api/app/routes/hardware.py` — Status-API (GET /hardware/status, GET /hardware/entropy)
- `apps/api/app/routes/kozyrev.py` — Kozyrev-Entropy-Endpunkt (aus radiquant4 portieren)
