# Architecture

## Overview

```
ZipAssist Cloud API (zipassist.zipindustries.com)
        │
        ▼
┌─────────────────────────────┐
│   ZipAssistClient           │  → aiohttp session, JWT auth
│   (client.py)               │    30 API methods
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│   ZipAssistCoordinator      │  → DataUpdateCoordinator
│   (coordinator.py)          │    polls every 300s
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│   Home Assistant Entities   │
│                             │
│   Each HydroTap → 1 Device  │
│   (via DeviceRegistry)      │
│                             │
│   18 sensors                │
│    1 binary sensor          │
│   20 switches               │
│   10 numbers                │
│    3 selects                │
│   18 times                  │
│   ─────────────────────     │
│   70 total entities         │
│    2 services               │
└─────────────────────────────┘
```

## Design Decisions

### 1. Each HydroTap = One HA Device
- Domain: `zipassist`
- Device identified by `hydrotapId` (UUID v4)
- Device name: `{buildingName} - {level}/{location}` e.g. `My Office - 1/Kitchen`
- Model (`moduleName`, e.g. "BC 100/75") stored in device `model` metadata

### 2. Coordinator Polling
- Default interval: 300 seconds (5 min)
- Fetches per cycle: hydrotap list, settings, settings-options, current faults, latest status log (per tap), sleep modes (shared)
- Each per-tap fetch is independently error-tolerant (one failing tap doesn't block others)

### 3. Settings Write (PATCH) Behaviour
The API's `PATCH /api/hydrotaps/{id}/settings` endpoint may return `200` or `204`
on success. The client (`update_settings`) accepts both. On failure, the response
status and body are logged at ERROR level for debugging.

Key details:
- **Headers:** `Content-Type: application/json` and `Accept: application/json` are sent explicitly.
- **401 retry:** If the token expired between the pre-check and the PATCH, the client re-authenticates and retries once.
- **Payload shape:** The PATCH body is a partial settings object — only the field(s) being changed are sent (e.g. `{"hotIsolationEnabled": true}`).

### 4. Sleep Mode Name Resolution
The `sleep_mode_status` sensor resolves numeric codes to human-readable names via `/api/sleep-modes` (fetched once by the coordinator, shared across all hydrotaps). The raw numeric code is exposed as a `sleep_mode_code` attribute. The `sleep_mode` select entity uses the same data for its options list.

### 5. Safety Toggles as Switches
`safety_lock` and `hot_isolation` are **writable switches** (in `switch.py`), not read-only binary sensors. They were removed from `binary_sensor.py` to avoid duplicate entities. Toggling them PATCHes the setting to the API.

### 6. Entity Icons
Every entity has an explicit `icon` or a `device_class` that implies one.

## File Structure

```
homeassistant-zipassist/
├── custom_components/
│   └── zipassist/
│       ├── __init__.py          # async_setup_entry, device registry
│       ├── manifest.json        # HA integration manifest
│       ├── config_flow.py       # UI config flow (email, password, reauth)
│       ├── const.py             # Domain, config keys, API paths
│       ├── client.py            # ZipAssistClient (auth + 30 API methods)
│       ├── coordinator.py       # DataUpdateCoordinator (300s polling)
│       ├── sensor.py            # 18 sensor entities
│       ├── binary_sensor.py     # 1 binary sensor (system_fault)
│       ├── switch.py            # 20 switch entities (safety + energy timers)
│       ├── number.py            # 10 number entities (temps, durations, filters)
│       ├── select.py            # 3 select entities (sleep, energy mode, sync)
│       ├── time.py              # 18 time entities (energy schedules)
│       ├── services.py          # 2 services (clear_fault, set_temperature)
│       ├── services.yaml        # Service definitions for HA
│       ├── helpers.py           # Shared helpers (device_name, etc.)
│       ├── strings.json         # i18n strings
│       └── translations/
│           └── en.json          # English translations
├── docs/                        # Documentation
├── exploration/
│   └── explore.py               # Live API exploration script
├── tests/
│   ├── conftest.py
│   ├── test_client.py
│   ├── test_config_flow.py
│   ├── test_coordinator.py
│   ├── test_entities.py
│   ├── test_helpers.py
│   └── test_services.py
├── tools/
│   ├── __init__.py
│   └── commands.py
├── .env / .env.example
├── .gitignore
├── pyproject.toml
├── hacs.json
├── LICENSE
└── README.md
```