# 03 — Spooky2 USB Radionics-Gerät: HAL-2.0-Treiber

> **Quelle:** `/opt/radiquant4/apps/api/app/services/hardware/`
> **Status in v5:** ❌ Nicht vorhanden — vollständige Migration erforderlich.

---

## 1. Unterstützte Hardware

### 1.1 Spooky2 XM Generator (Primärpfad)

| Eigenschaft | Wert |
|---|---|
| **Chip** | CH341 USB-Serial Controller |
| **VID/PID** | `0x1A86 / 0x7523` (primary), `0x1A86 / 0x5523` (secondary) |
| **Baud-Rate** | 115200 |
| **Protokoll** | `rq4-spooky2-scaffold-v1` (proprietärer Frame-Typ) |

### 1.2 GeneratorX Pro (Sekundärpfad)

| Eigenschaft | Wert |
|---|---|
| **Chip** | CH343 USB-Serial Controller |
| **VID/PID** | `0x1A86 / 0x55D2` bis `0x55DA` (7 Varianten) |
| **Baud-Rate** | 115200 |

### 1.3 Legacy HID Fallback

| Eigenschaft | Wert |
|---|---|
| **VID/PID** | `0x10C4 / 0xEA60` (Silicon Labs CP210x) |
| **Protokoll** | USB-HID, 64-Byte Reports |

---

## 2. Architektur: `Spooky2Driver` (HAL-2.0)

**Datei:** `apps/api/app/services/hardware/spooky2_driver.py` (828 Zeilen)

### 2.1 Klassen-Hierarchie

```
BaseHardwareDriver
    └── Spooky2Driver
            ├── _cpu_gpu_entropy_driver: CPUGPUEntropyDriver   (Virtual Mode)
            └── _kozyrev_driver: KozyrevEntropyDriver           (Virtual Mode)
```

### 2.2 Verbindungslogik (Priorität)

```
connect()
    1. _connect_serial_transport()     → CH341/CH343 USB-Serial Discovery
       ├── Expliziter Port (config["port"])
       └── Auto-Discovery via serial.tools.list_ports
    2. _connect_legacy_hid_transport() → Silicon Labs HID (Fallback)
    3. _activate_virtual_mode()        → Entropie-basierter Virtual Mode (immer vorhanden)
```

### 2.3 Serial Frame-Protokoll

Da das proprietäre Spooky2-Protokoll **nicht öffentlich dokumentiert** ist, wurde ein versionierter Frame-Scaffold implementiert:

```
Frame-Struktur: STX(0x02) VER(0x10) OPCODE LEN[2] PAYLOAD CHECKSUM ETX(0x03)

Opcodes:
    0xA0 = Handshake
    0xF1 = emit_signal (Einzelfrequenz)
    0xF2 = emit_program (Frequenz-Programm)

Checksum: sum(frame[1:-2]) & 0xFF
```

**ACK-Erkennung:** `0x06` (Byte-ACK) oder framed JSON mit `{"ack": true}`.

### 2.4 Preset-Mapping

```
PresetMappingService
    └── Root: /opt/radiquant4/spooky2/Preset Collections/
        ├── Sammlungs-Verzeichnisse (automatisch gescannt)
        └── map_to_frequency_sequence(emission_program, context) → Preset-Sequenz
```

---

## 3. Virtual Mode (Offline-Fallback)

Wenn keine Hardware verbunden ist, wechselt der Treiber automatisch in den **Virtual Mode**. Dabei wird ein synthetisches ACK aus Hardware-Entropie erzeugt:

```python
async def _generate_virtual_ack(self, fallback_context) -> dict:
    cpu_entropy = await cpu_driver.read_entropy(sample_count=6)
    kozyrev_entropy = await kozyrev_driver.read_entropy(sample_count=4)

    combined_entropy = (
        cpu_entropy["cpu"]        * 0.24
        + cpu_entropy["ram"]      * 0.24
        + cpu_entropy["gpu"]      * 0.12
        + kozyrev_entropy["cpu"]  * 0.12
        + kozyrev_entropy["quartz"] * 0.16    # ← Quarz-Signatur eingebaut
        + kozyrev_entropy["combined"] * 0.12
    )
    # → Virtual-ACK enthält entropy_snapshot + kozyrev_snapshot + combined_entropy
```

**Wichtig:** Im Virtual Mode emittiert der Treiber **keine physische Frequenz**. Der Virtual Mode dient der Entwicklung und wenn Hardware nicht verfügbar ist.

---

## 4. HALManager — Zentrale Geräteverwaltung

**Datei:** `apps/api/app/services/hardware/hal_manager.py` (879 Zeilen)

### 4.1 Modi

| Modus | Beschreibung |
|---|---|
| `REAL` | USB-HID/Serial Hardware direkt |
| `WEBRTC` | Frequenz-Emission via Browser/WebRTC-Bridge (Client-seitig) |
| `SIMULATION` | MockGeneratorDriver (immer verfügbar) |
| `AUTO` | Priorität: REAL → WEBRTC → SIMULATION |

### 4.2 Geräteregistrierung

```python
hal = get_hal_manager()
hal.register_device(DeviceConfig(
    device_id="spooky2-main",
    device_type="spooky2",
    mode=HardwareMode.AUTO,
    vendor_id=0x1A86,
    product_id=0x7523,
    extra_config={
        "preset_catalog_root": "/opt/radiquant4/spooky2/Preset Collections",
        "virtual_use_gpu": True,
        "kozyrev_tree_depth": 12,
        "kozyrev_alpha": 0.5,
    }
))
```

### 4.3 Capabilities (Spooky2 Standard)

```python
DeviceCapabilities(
    parallel_channels=8,
    supported_waveforms=("sine", "square", "triangle", "sawtooth", "custom"),
    ack_type="device_ack",
    supports_atomic_program=True,
)
```

### 4.4 Atomic Program Dispatch

Bei `supports_atomic_program=True` und `mode="simultaneous"` werden alle Frequenzen in einem einzigen Frame übertragen (`emit_program_atomic`). Andernfalls wird iterativ gesendet.

---

## 5. SSE-Events bei Hardware-Ereignissen

Der Treiber emittiert folgende SSE-Events bei Statusänderungen:

| Event | Auslöser | Funktion |
|---|---|---|
| `hardware.ack_received` | Erfolgreicher ACK vom Gerät | `emit_hardware_ack_received()` |
| `hardware.disconnected` | Verbindungsverlust | `emit_hardware_disconnected()` |
| `hardware.fallback_active` | Wechsel in Virtual Mode | `emit_fallback_active()` |

**Datei:** `apps/api/app/services/realtime_event_bus.py` — alle drei Emit-Funktionen.

---

## 6. Python-Abhängigkeiten

| Paket | Optional? | Zweck |
|---|---|---|
| `pyserial` | **Ja** — serial import in try/except | CH341/CH343 USB-Serial |
| `hid` (hidapi) | **Ja** — hid import in try/except | Legacy HID-Fallback |

Wenn weder `pyserial` noch `hid` installiert sind, startet der Treiber direkt im Virtual Mode.

---

## 7. Preset Collections

Das System erwartet eine Preset-Verzeichnisstruktur unter `/opt/radiquant4/spooky2/Preset Collections/`. Diese enthält die Spooky2 Preset-Sammlungen (proprietäre Spooky2-Dateien, nicht im Repo eingecheckt). `Spooky2PresetCatalogPlaceholder` scannt das Verzeichnis und macht Sammlungen als Treiber-Fähigkeit sichtbar.

**Snapshot-Output:**
```json
{
    "root_path": "/opt/radiquant4/spooky2/Preset Collections",
    "collection_count": 42,
    "collections_preview": ["BFB-Database", "Cancer", "Detox", ...]
}
```

---

## 8. Betroffene Dateien (Vollständig)

| Datei | Rolle |
|---|---|
| `apps/api/app/services/hardware/spooky2_driver.py` | **Haupt-Treiber** — Serial/HID/Virtual, Frame-Builder, ACK-Parser |
| `apps/api/app/services/hardware/hal_manager.py` | **HAL-Manager** — Geräteverwaltung, AUTO-Modus, Statistiken |
| `apps/api/app/services/hardware/serial_driver.py` | Basis-Serial-Utilities (gemeinsam mit Spooky2) |
| `apps/api/app/services/hardware/preset_mapping_service.py` | Preset-Kollektion → Frequenz-Sequenz-Mapping |
| `apps/api/app/services/hardware/mock_driver.py` | MockGeneratorDriver (SIMULATION-Fallback) |
| `apps/api/app/services/hardware/webrtc_bridge_service.py` | WebRTC-Bridge (WEBRTC-Modus) |
| `apps/api/app/services/hardware/webrtc_driver.py` | WebRTC-Hardware-Driver |
| `apps/api/app/services/hardware/hotplug_monitor.py` | USB-Hotplug-Überwachung (auto-reconnect) |
| `apps/api/app/services/hardware/hardware_state.py` | Globaler Hardware-Zustandsspeicher |
| `apps/api/app/services/hardware/registry.py` | Treiber-Registry (Typ → Klasse) |
| `apps/api/app/services/realtime_event_bus.py` | SSE-Events für Hardware-Ereignisse |
