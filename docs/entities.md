# Entities

The integration exposes **74 entities** across 6 platforms for each HydroTap device.

## Device Naming

- **Device name:** `{buildingName} - {level}/{location}` e.g. `My Office - 1/Kitchen`
- **Model** (`moduleName`) is stored as device `model` metadata, e.g. `BC 100/75`
- The generic "HydroTap" label from the API is discarded

## Platform Summary

| Platform | File | Count | Notes |
|---|---|---|---|
| Sensor | `sensor.py` | 18 | Filter life, usage, status, diagnostics, status log fields |
| Binary Sensor | `binary_sensor.py` | 1 | `system_fault` (PROBLEM device class) |
| Switch | `switch.py` | 22 | Safety toggles (2) + energy timer actives (20) |
| Number | `number.py` | 10 | Temps (2), dispense durations (4), filter limits (4) |
| Select | `select.py` | 3 | Sleep mode, energy mode, sync period |
| Time | `time.py` | 20 | Energy on/off schedule times |
| **Total** | | **74** | |

## Services

| Service | Description |
|---|---|
| `zipassist.clear_system_fault` | Clear a fault by `device_id` + `fault_id` |
| `zipassist.set_temperature` | Set boiling/chilled temp by `device_id` + `water_type` + `temperature` |

## Entity Icons Reference

### Sensors (`sensor.py`) — 18 entities

| Entity key | Icon | Notes |
|---|---|---|
| `filter_litres_remaining` | `mdi:water-opacity` | |
| `filter_days_remaining` | `mdi:calendar-clock` | |
| `filter_estimated_days` | `mdi:calendar-sync` | |
| `average_daily_usage` | `mdi:water-percent` | |
| `peak_hourly_usage` | `mdi:water-sync` | |
| `last_sync` | _(none)_ | Uses `device_class: TIMESTAMP`. HA entity UI and the ZipAssist card show relative time ("X ago"); the card tooltip shows absolute local time. |
| `status` | `mdi:information-outline` | |
| `serial_number` | `mdi:numeric` | |
| `firmware_version` | `mdi:chip` | |
| `system_fault_details` | `mdi:alert-circle` | |
| `wifi_signal_strength` | _(none)_ | Uses `device_class: SIGNAL_STRENGTH` |
| `energy_since_last_log` | _(none)_ | Uses `device_class: ENERGY` |
| `energy_total` | _(none)_ | Uses `device_class: ENERGY` |
| `sleep_mode_status` | `mdi:sleep` | Code resolved to name via `/api/sleep-modes` |
| `litres_filtered_internal` | `mdi:water-filter` | |
| `litres_filtered_external` | `mdi:water-filter` | |
| `days_filtered_internal` | `mdi:calendar-check` | |
| `days_filtered_external` | `mdi:calendar-check` | |

### Numbers (`number.py`) — 10 entities

| Entity key | Icon | Notes |
|---|---|---|
| `boiling_temp` | `mdi:thermometer-high` | |
| `chilled_temp` | `mdi:thermometer-low` | |
| `boiling_duration` | `mdi:timer-outline` | |
| `chilled_duration` | `mdi:timer-outline` | |
| `sparkling_duration` | `mdi:timer-outline` | |
| `ambient_duration` | `mdi:timer-outline` | |
| `internal_filter_litres` | `mdi:water-filter` | |
| `internal_filter_days` | `mdi:calendar-clock` | |
| `external_filter_litres` | `mdi:water-filter` | |
| `external_filter_days` | `mdi:calendar-clock` | |

### Switches (`switch.py`) — 22 entities

| Entity key | Icon | Notes |
|---|---|---|
| `safety_lock` | `mdi:lock` | Writable — PATCHes `safetyLockEnabled` |
| `hot_isolation` | `mdi:water-off` | Writable — PATCHes `hotIsolationEnabled` |
| All timer on/off switches (20) | `mdi:timer-play-outline` / `mdi:timer-stop-outline` | |

### Binary Sensors (`binary_sensor.py`) — 1 entity

| Entity key | Icon | Notes |
|---|---|---|
| `system_fault` | _(none)_ | Uses `device_class: PROBLEM`. Read-only diagnostic. |

> **Note:** `safety_lock` and `hot_isolation` are **switches** (in `switch.py`), not binary sensors.

### Selects (`select.py`) — 3 entities

| Entity key | Icon | Notes |
|---|---|---|
| `sleep_mode` | `mdi:sleep` | |
| `energy_mode` | `mdi:power-plug` | |
| `sync_period` | `mdi:sync` | |

### Times (`time.py`) — 20 entities

| Entity key | Icon | Notes |
|---|---|---|
| All on-time entities | `mdi:clock-start` | |
| All off-time entities | `mdi:clock-end` | |