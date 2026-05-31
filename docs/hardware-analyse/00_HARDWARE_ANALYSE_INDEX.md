# Hardware-Analyse: Kozyrev / Quarz / QRNG / Spooky2

> **Erstellt:** 2026-05-30 · Cascade Tiefenanalyse vor W3-Start.
> **Quellbasis:** `/opt/radiquant4` (Produktiv-Implementierung), `/opt/radiquant-v5` (Zielrepo — aktuell NICHT integriert).
> **Zweck:** Vollständige Bestandsaufnahme aller Hardware-Strukturen und Algorithmen für die Migration nach v5.

## Dokumente in diesem Ordner

| Datei | Inhalt |
|---|---|
| `01_KOZYREV_STRUKTUREN.md` | Kozyrev-Entropy-Driver (CPU/GPU), p-adische Wavelets, Vladimirov-Operator, Torsionsfeld, Quarz-Signatur |
| `02_QRNG_PRNG_ENTROPY.md` | Quantenzufallsgenerator (QRNG via pyqrng/Quantis), TRNG-Kaskade, Software-Fallback (os.urandom), Entropy-Pool-Service |
| `03_SPOOKY2_USB_TREIBER.md` | Spooky2 XM / GeneratorX Pro USB-Serial-Treiber (CH341/CH343), HID-Fallback, Virtual-Mode, HAL-Manager-Integration |
| `04_QUARZ_HARDWARE_ALGORITHMEN.md` | Quarz-Kohärenz-Messung (algorithmisch / software-basiert), 32.768 kHz Referenz, _measure_quartz_signature |
| `05_V5_MIGRATIONSPFAD.md` | Status in v5 (aktuell: NICHT vorhanden), empfohlene Migrationsstrategie, Feature-Flags, Abhängigkeiten |

## Kurzübersicht: Was ist integriert, wo?

| Komponente | radiquant4 Status | radiquant-v5 Status |
|---|---|---|
| KozyrevEntropyDriver (CPU p-adische Wavelets) | ✅ Vollständig implementiert | ❌ Nicht vorhanden |
| KozyrevEntropyDriver (GPU CUDA Haar-Wavelets) | ✅ Vollständig implementiert | ❌ Nicht vorhanden |
| KozyrevDiodeDriver (Raspberry Pi GPIO) | ✅ Implementiert, GPIO optional | ❌ Nicht vorhanden |
| TorsionFieldGenerator (Φ = α·|dS/dt|·f(T,ω)) | ✅ Implementiert | ❌ Nicht vorhanden |
| Quarz-Signatur (algorithmisch, 32.768 kHz) | ✅ In KozyrevEntropyDriver | ❌ Nicht vorhanden |
| QRNG (pyqrng / Quantis USB) | ✅ EntropySource, lazy-optional | ❌ Nicht vorhanden |
| QRNG Software-Fallback (os.urandom / CRNG) | ✅ TRNGSource.OS_URANDOM | ❌ Nicht vorhanden |
| Spooky2 Driver (USB-Serial CH341/CH343) | ✅ Vollständiger HAL-2.0-Treiber | ❌ Nicht vorhanden |
| Spooky2 HID Legacy Fallback | ✅ Vorhanden | ❌ Nicht vorhanden |
| Spooky2 Virtual Mode (Entropie-basiert) | ✅ Vollständig implementiert | ❌ Nicht vorhanden |
| EntropyPoolService (Singleton, Ringbuffer) | ✅ Mit Redis-Lease-Isolation | ❌ Nicht vorhanden |
| HALManager (AUTO/REAL/WEBRTC/SIMULATION) | ✅ Vollständiger Manager | ❌ Nicht vorhanden |
| CPUGPUEntropyDriver (AMD RDRAND/RDSEED) | ✅ Implementiert | ❌ Nicht vorhanden |
| TRNG-Kaskade (QRNG→WebCam→InfNoise→ESP32→urandom) | ✅ Architektur vorhanden, teils Placeholder | ❌ Nicht vorhanden |
