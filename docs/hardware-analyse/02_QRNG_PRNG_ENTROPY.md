# 02 — QRNG / PRNG / Kryptografischer Entropie-Stack

> **Quellen:**
> - `/opt/radiquant4/apps/api/app/services/hardware/entropy_sources.py` (Morphic_Engine_V2 Provider)
> - `/opt/radiquant4/apps/api/app/services/hardware/seed_generator.py`
> - `/opt/radiquant4/apps/api/app/services/hardware/entropy_pool.py`
> **Status in v5:** ❌ Nicht vorhanden — vollständige Migration erforderlich.

---

## 1. Überblick: Entropie-Quellen-Hierarchie

Das System implementiert eine **mehrstufige TRNG-Kaskade** mit automatischem Fallback:

```
QRNG (Quantis USB / pyqrng)
    ↓ Fallback wenn nicht vorhanden
HID-Sensor (VID 0x0E50 / PID 0x0002)
    ↓ Fallback
WebCam-Hotbits             [Architektur vorbereitet, Placeholder]
    ↓ Fallback
Infinite Noise TRNG (Leetronics USB) [Architektur vorbereitet, Placeholder]
    ↓ Fallback
ESP32 TRNG (seriell)       [Architektur vorbereitet, Placeholder]
    ↓ Fallback (IMMER verfügbar)
os.urandom (Betriebssystem-CRNG)
```

---

## 2. QRNG — Quantenzufallsgenerator-Hardware

### 2.1 Hardware-Klasse: `QrngSource`

**Datei:** `modules/entwickelte-module/Radimorphic/Morphic_Engine_V2/providers/hardware/entropy_sources.py` (Zeile 123)

```python
class QrngSource(EntropySource):
    """Quantis USB / QRNG-Geräte via pyqrng (falls vorhanden)."""

    def healthy(self) -> bool:
        return pyqrng is not None

    def sample_h_level(self, duration_s: float = 1.0) -> float:
        n = int(max(128, duration_s * 256))
        data = pyqrng.get_random_data(n)  # returns bytes
        arr = np.frombuffer(data, dtype=np.uint8)
        ent = _spectral_entropy(arr)
        std_n = clamp(np.std(arr) / 128.0)
        return 0.6 * ent + 0.4 * std_n
```

**Voraussetzung:** `pip install pyqrng` + physisches Quantis-USB-Gerät (ID Quantique).
**Lazy Import:** `import pyqrng` wird in `try/except` umschlossen — kein Fehler wenn nicht installiert.
**Entropie-Berechnung:** 60% Spektrale Entropie (FFT-basiert) + 40% Standardabweichung.

### 2.2 Spektrale Entropie-Funktion

```python
def _spectral_entropy(arr: np.ndarray) -> float:
    """Shannon-Entropie im Frequenzbereich (normalisiert [0,1])."""
    x = arr.astype(np.float64) - np.mean(arr)
    p = np.abs(np.fft.rfft(x))[1:] ** 2
    p = p / p.sum()
    H = -np.sum(p * np.log2(p[p > 0]))
    return clamp(H / np.log2(len(p)))
```

---

## 3. Software-Alternative: Kryptografisch sicherer PRNG

### 3.1 `os.urandom` — CRNG Fallback

**Datei:** `apps/api/app/services/hardware/entropy_pool.py` (Zeile 196)

```python
async def get_entropy_bytes(self, tenant_id, session_id, count=32) -> bytes:
    base_entropy = os.urandom(count)           # OS-CRNG (Linux: getrandom syscall)

    isolated_data = await self.get_isolated_entropy(tenant_id, session_id, sample_count=1)
    score = isolated_data.get("combined", 50.0)

    # XOR-Modulation für radionische Integrität
    mod_byte = int(score * 2.55) % 256
    return bytes([b ^ mod_byte for b in base_entropy])
```

**Sicherheitsniveau:** `os.urandom` auf Linux nutzt den Kernel-CRNG (getrandom/urandom), der nach FIPS 140-2 als kryptografisch sicher gilt. **Kein `crypto.getRandomValues` (Frontend) vorhanden** — Backend nutzt ausschließlich `os.urandom`.

### 3.2 TRNG-Fallback-Kaskade in `seed_generator.py`

**Datei:** `apps/api/app/services/hardware/seed_generator.py`

```python
class TRNGSource(str, Enum):
    QRNG = "qrng"                    # → EntropyPoolService (Kozyrev/QRNG)
    WEBCAM = "webcam"                # Placeholder (nicht implementiert)
    INFINITE_NOISE = "infinite_noise" # Placeholder (nicht implementiert)
    ESP32 = "esp32"                  # Placeholder (nicht implementiert)
    OS_URANDOM = "os_urandom"        # immer verfügbar

async def get_trng_bytes(tenant_id, session_id, count=8) -> tuple[bytes, TRNGSource]:
    # Versucht QRNG → WebCam → InfNoise → ESP32 → os.urandom
```

**Wichtig:** `QRNG`-Pfad in dieser Kaskade ruft den `EntropyPoolService` auf, der intern den `KozyrevEntropyDriver` nutzt — NICHT direkt ein QRNG-Gerät. Die Benennung `QRNG` ist konzeptionell gemeint.

---

## 4. EntropyPoolService (Singleton)

**Datei:** `apps/api/app/services/hardware/entropy_pool.py`

### 4.1 Architektur

```
EntropyPoolService (Singleton)
├── KozyrevEntropyDriver (use_gpu=True)
├── RedisLockManager (Session-Isolation via Lease)
├── _cpu_buffer: deque(maxlen=100)    # Ring-Buffer für CPU-Entropie
└── _gpu_buffer: deque(maxlen=100)    # Ring-Buffer für GPU-Entropie
```

### 4.2 Session-Tainting (Datenisolation)

Jede Session erhält **tainierten** Entropie-Output:

```python
async def get_isolated_entropy(self, tenant_id, session_id, sample_count=10) -> dict:
    # Holt Entropie mit Redis-Lease (verhindert gleichzeitigen Hardware-Zugriff)
    # Taint-Faktor: SHA256(tenant_id + session_id + timestamp)[:8]
    # → Jede Session bekommt deterministisch unterschiedliche Modulation
```

### 4.3 Kontinuierliches Sampling

```python
async def start(self):
    """Startet Hintergrund-Task für kontinuierliches Entropie-Sampling."""
    self._task = asyncio.create_task(self._sampling_loop())

async def _sampling_loop(self):
    while self._is_running:
        data = await self._driver.read_entropy(sample_count=3)
        self._cpu_buffer.append(data["cpu"])
        self._gpu_buffer.append(data["gpu"])
        await asyncio.sleep(0.1)  # 10 Hz Sampling-Rate
```

---

## 5. GPU-basierte Entropie: `GpuSource`

**Datei:** `entropy_sources.py` (Zeile 149)

```python
class GpuSource(EntropySource):
    """GPU-basierte Entropiequelle über CuPy/CUDA."""

    def sample_h_level(self, duration_s=1.5) -> float:
        # Misst Laufzeit-Jitter von kleinen GPU-Matrizenoperationen (64×64)
        # rel_jitter = std(times) / mean(times) → normiert auf [0,1]
```

**Prinzip:** Quantenrauschen in NVIDIA GPU-Tensor-Cores manifestiert sich als Ausführungszeit-Jitter bei identischen Berechnungen. Dieser Jitter wird als Entropie-Maß verwendet.

---

## 6. Weitere Entropie-Klassen (entropy_sources.py)

| Klasse | Quelle | Status |
|---|---|---|
| `CpuTimerSource` | Timer-Jitter + CPU-Varianzen + Time-Coherence | ✅ Immer verfügbar |
| `HidSource` | HID-Gerät (VID 0x0E50, PID 0x0002) | Optional, lazy |
| `QrngSource` | pyqrng (Quantis USB) | Optional, lazy |
| `GpuSource` | CuPy CUDA Matrizenoperationen | Optional, lazy |
| `NetworkSource` | HTTP/WebSocket RTT-Jitter | Optional, via Env-Var |
| `MockSource` | Fester Wert (Tests) | Nur Tests |

**Auswahllogik:**
```python
def select_entropy_source(preferred=None) -> EntropySource:
    order = preferred or ["qrng", "hid_sensor", "cpu_timer"]
    # Erste verfügbare Quelle nach Priorität
```

---

## 7. Betroffene Dateien (Vollständig)

| Datei | Rolle |
|---|---|
| `apps/api/app/services/hardware/entropy_pool.py` | **Haupt-Service** — Singleton, Session-Isolation, XOR-Modulation, `get_entropy_bytes` |
| `apps/api/app/services/hardware/seed_generator.py` | **TRNG-Kaskade** — `TRNGSource`, `get_trng_bytes`, `generate_radionic_seeds_with_trng` |
| `modules/entwickelte-module/Radimorphic/Morphic_Engine_V2/providers/hardware/entropy_sources.py` | **Entropie-Quellen** — QrngSource, GpuSource, HidSource, CpuTimerSource, NetworkSource |
| `apps/api/app/routes/kozyrev.py` | **API-Endpunkt** GET `/entropy` — Exposes Kozyrev-Entropie-Metriken |
| `apps/api/app/services/hardware/kozyrev_driver.py` | Liefert `_read_cpu/gpu_kozyrev_entropy` an EntropyPool |

---

## 8. v5-Migrationsnote: `crypto.getRandomValues`

Der User fragte nach `crypto.getRandomValues` als Frontend-Alternative. **In radiquant4 gibt es kein Frontend-PRNG** — alle Zufallszahlen werden server-seitig erzeugt. Die Entsprechung für v5 wäre:

| radiquant4 (Python) | Äquivalent für v5 Frontend (TypeScript) |
|---|---|
| `os.urandom(n)` | `crypto.getRandomValues(new Uint8Array(n))` |
| `EntropyPoolService.get_entropy_bytes()` | Kein Frontend-Äquivalent — Backend-API-Call |
| `KozyrevEntropyDriver.read_entropy()` | Backend-only — nicht ins Frontend portieren |

**Empfehlung für v5:** Frontend bleibt Thin-Client (wie in B.3 festgelegt). Kein lokales PRNG im Frontend — alle Entropie kommt über Backend-Endpunkte.
