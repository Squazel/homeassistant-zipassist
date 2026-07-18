# ZipAssist CMMS — Home Assistant Integration Plan

> **Status:** ✅ Core complete — 70 entities across 6 platforms, 2 services, config flow, full API client (30 methods). See [Implementation Status](#implementation-status) for details.

## Implementation Status

| Area | Status | Details |
|---|---|---|
| Config flow (UI auth) | ✅ Done | Email + password + optional base_url; reauth support |
| Coordinator polling | ✅ Done | 300s interval; fetches hydrotaps, settings, options, faults, logs, sleep modes |
| API client | ✅ Done | 30 methods covering all known endpoints; JWT auth with auto-refresh |
| Sensor platform | ✅ Done | 18 sensors (filter life, usage, status, diagnostics) |
| Binary sensor platform | ✅ Done | 1 binary sensor (`system_fault`) |
| Switch platform | ✅ Done | 20 switches (safety toggles + energy timer actives) |
| Number platform | ✅ Done | 10 numbers (temps, durations, filter limits) |
| Select platform | ✅ Done | 3 selects (sleep mode, energy mode, sync period) |
| Time platform | ✅ Done | 18 time entities (energy on/off schedules) |
| Services | ✅ Done | `clear_system_fault`, `set_temperature` |
| Entity icons | ✅ Done | All entities have explicit icons or device_class |
| Sleep mode name resolution | ✅ Done | Numeric codes resolved to names via `/api/sleep-modes` |
| Safety toggles as switches | ✅ Done | `safety_lock` & `hot_isolation` are writable switches (not binary sensors) |
| PATCH error handling | ✅ Done | Accepts 200/204; logs failures with status + body |
| Tests | 🔲 Partial | Unit tests exist for client, config_flow, coordinator, helpers, services |
| HACS submission | 🔲 Pending | `hacs.json` exists but not yet submitted |
| PIN settings entity | 🔲 Not started | `security.pin` in settings not exposed |
| Language select | 🔲 Not started | `language` field in settings not exposed |
| Allow safety setting change | 🔲 Not started | `allowSafetySettingChange` toggle not exposed |
| Zip managed indicator | 🔲 Not started | `zipManaged` flag not exposed as entity |
| Usage graphs in HA | 🔲 Not started | API methods exist but no HA sensors/entities consume them |
| Notes read/write | 🔲 Not started | API methods exist but no HA entities consume them |

## Architecture Overview

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
│   ✅ 18 sensors             │
│   ✅  1 binary sensor       │
│   ✅ 20 switches            │
│   ✅ 10 numbers             │
│   ✅  3 selects             │
│   ✅ 18 times               │
│   ─────────────────────     │
│   ✅ 70 total entities      │
│   ✅  2 services            │
└─────────────────────────────┘
```

## Authentication

**Flow:** HTTP Basic → JWT Bearer

1. `GET /api/auth/jwt/login` with header `Authorization: Basic <base64(email:password)>`
2. Response: `{ "token": "<jwt>", "user": { "name": "...", "userType": "owner|admin|facilityManager", ... } }`
3. All subsequent requests: header `Authorization: Bearer <token>`
4. Refresh: `GET /api/auth/jwt/refresh` (returns new token when near expiry)

**Credentials:** Stored in `.env` (dev) / HA config entry (prod).

## API Endpoints (verified via browser + script)

All endpoints are prefixed with `/api`. The hydrotap UUID used for testing: `631a3385-301b-4c9c-97ed-3a1a50061f5c`.

### Hydrotap Listing
| Method | Path | Role | Purpose |
|--------|------|------|---------|
| GET | `/api/hydrotaps` | admin | Search all hydrotaps |
| GET | `/api/owners/{ownerId}/hydrotaps` | owner | List owner's hydrotaps |
| GET | `/api/owners/{ownerId}/hydrotaps-without-system-faults` | owner | Taps without alerts |

The list response includes 30 fields:
```
hydrotapId, serialNumber, moduleName, firmwareVersion, calibrationDate,
status, zipManaged, connectionKey, filterLifeRemainingLitres,
filterLifeRemainingDays, filterLifeRemainingEstimated, averageDailyUsage,
peakHourlyUsage, hydrotapLocation (buildingName, level, locationInBuilding,
country, state), ownerCompanyName, facilityManagerCompanyName,
permissions {view, edit}, hydrotapGroups[], groupName, lastSyncTimestamp
```

### Hydrotap Detail & Settings

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/hydrotaps/{id}` | Hydrotap detail (location, serial, firmware, status, filter life, etc.) |
| GET | `/api/hydrotaps/{id}/settings` | Current settings (temperature, dispense, filters, energy, safety, etc.) |
| GET | `/api/hydrotaps/{id}/settings-options` | Allowed ranges/options for each setting |
| PATCH | `/api/hydrotaps/{id}/settings` | Write settings — body is the same shape as GET settings |
| GET | `/api/hydrotaps/{id}/timezone` | Returns `{ "timezone": "Australia/Sydney" }` |

### Logs & Usage

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/hydrotaps/{id}/logs/general?page=0&perPage=10` | Status logs (energy, filter litres, wifi, sleep mode) |
| GET | `/api/hydrotaps/{id}/logs/general?limit=1&withSmartEstimate=true` | Latest status log |
| GET | `/api/hydrotaps/{id}/logs/system-faults?currentOnly=true` | Active system faults |
| GET | `/api/hydrotaps/{id}/logs/filter-usage?page=0&perPage=10` | Filter usage history |
| GET | `/api/hydrotaps/{id}/logs/filter-usage?limit=1&type=internal` | Latest internal filter usage |
| GET | `/api/hydrotaps/{id}/logs/filter-usage?limit=1&type=external` | Latest external filter usage |
| GET | `/api/hydrotaps/{id}/logs/dispense-events?page=0&perPage=10` | Dispense events |
| GET | `/api/hydrotaps/{id}/logs/daily-usage?limit=1` | Daily usage summary |
| GET | `/api/hydrotaps/{id}/usage/water?minDate=...&maxDate=...&timezoneOffset=...` | Water usage data |
| GET | `/api/hydrotaps/{id}/usage/energy?minDate=...&maxDate=...&timezoneOffset=...` | Energy usage data |
| GET | `/api/hydrotaps/{id}/graphs/usage?minDate=...&maxDate=...&timezoneOffset=...` | Graph series data |
| GET | `/api/hydrotaps/{id}/graphs/average-usage?minDate=...&maxDate=...&timezoneOffset=...` | Average usage graph |

### Faults & Alerts

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/system-faults` | Fault code definitions |
| GET | `/api/system-events` | System event definitions |
| PATCH | `/api/hydrotaps/{id}/system-faults/{faultId}` | Clear a fault (body: `{"endTimestamp": "..."}`) |

### Hydrotap Search (Admin)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/hydrotaps?perPage=10&page=0&search=<base64json>` | Search all hydrotaps |
| GET | `/api/hydrotap-search-options` | Filter option metadata |

### Owner-specific Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/owners/{ownerId}/hydrotaps` | List owner's hydrotaps |
| GET | `/api/owners/{ownerId}/hydrotap-groups` | Owner's groups |
| GET | `/api/owners/{ownerId}/hydrotap-system-faults/major` | Fault dashboard data |
| GET | `/api/owners/{ownerId}/hydrotap-system-faults/minor` | Alert dashboard data |
| GET | `/api/owners/{ownerId}/hydrotaps-without-system-faults` | Nominal taps |

### Other

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/sleep-modes/{id}` | Available sleep mode options |
| GET | `/api/countries` | Country list |
| GET | `/api/timezones` | Timezone list |
| GET | `/api/hydrotaps/{id}/notes` | Admin notes for a tap |
| POST | `/api/hydrotaps/{id}/notes` | Add a note |

## HA Integration Design Decisions

### 1. Each HydroTap = One HA Device ✅
- Domain: `zipassist`
- Device identified by `hydrotapId` (UUID v4)
- Device name: `{buildingName} - {level}/{location}` e.g. `The Warehouse - 1/Kitchen`
- Model (`moduleName`, e.g. "BC 100/75") stored in device `model` metadata
- The generic "HydroTap" label from the API is discarded

### 2. Coordinator polling ✅
- Default interval: 300 seconds (5 min)
- Fetches per cycle: hydrotap list, settings, settings-options, current faults, latest status log (per tap), sleep modes (shared)
- Each per-tap fetch is independently error-tolerant (one failing tap doesn't block others)

### 3. Entity Platforms ✅

| Platform | File | Count | Notes |
|---|---|---|---|
| Sensor | `sensor.py` | 18 | Filter life, usage, status, diagnostics, status log fields |
| Binary Sensor | `binary_sensor.py` | 1 | `system_fault` (PROBLEM device class) |
| Switch | `switch.py` | 20 | Safety toggles (2) + energy timer actives (18) |
| Number | `number.py` | 10 | Temps (2), dispense durations (4), filter limits (4) |
| Select | `select.py` | 3 | Sleep mode, energy mode, sync period |
| Time | `time.py` | 18 | Energy on/off schedule times |
| **Total** | | **70** | |

### 4. Services ✅

| Service | File | Description |
|---|---|---|
| `zipassist.clear_system_fault` | `services.py` + `services.yaml` | Clear a fault by `device_id` + `fault_id` |
| `zipassist.set_temperature` | `services.py` + `services.yaml` | Set boiling/chilled temp by `device_id` + `water_type` + `temperature` |

### 5. Settings Write (PATCH) Behaviour ✅

The API's `PATCH /api/hydrotaps/{id}/settings` endpoint may return `200` or `204`
on success. The client (`update_settings`) accepts both. On failure, the response
status and body are logged at ERROR level for debugging.

Key details:
- **Headers:** `Content-Type: application/json` and `Accept: application/json` are sent explicitly.
- **401 retry:** If the token expired between the pre-check and the PATCH, the client re-authenticates and retries once.
- **Payload shape:** The PATCH body is a partial settings object — only the field(s) being changed are sent (e.g. `{"hotIsolationEnabled": true}`).

### 6. Sleep Mode Name Resolution ✅
The `sleep_mode_status` sensor resolves numeric codes to human-readable names via `/api/sleep-modes` (fetched once by the coordinator, shared across all hydrotaps). The raw numeric code is exposed as an `sleep_mode_code` attribute. The `sleep_mode` select entity uses the same data for its options list.

### 7. Safety Toggles as Switches ✅
`safety_lock` and `hot_isolation` are **writable switches** (in `switch.py`), not read-only binary sensors. They were removed from `binary_sensor.py` to avoid duplicate entities. Toggling them PATCHes the setting to the API.

### 8. Entity Icons ✅
Every entity has an explicit `icon` or a `device_class` that implies one. See the [Entity Icons](#entity-icons-reference) reference table below.

## Entity Icons Reference

All entities have explicit icons or device_class. ✅ = complete.

#### Sensors (`sensor.py`) — 18 entities

| Entity key | Icon | Notes |
|---|---|---|
| `filter_litres_remaining` | `mdi:water-opacity` | |
| `filter_days_remaining` | `mdi:calendar-clock` | |
| `filter_estimated_days` | `mdi:calendar-sync` | |
| `average_daily_usage` | `mdi:water-percent` | |
| `peak_hourly_usage` | `mdi:water-sync` | |
| `last_sync` | _(none)_ | Uses `device_class: TIMESTAMP` |
| `status` | `mdi:information-outline` | |
| `serial_number` | `mdi:numeric` | |
| `firmware_version` | `mdi:chip` | |
| `system_fault_details` | `mdi:alert-circle` | ✅ |
| `wifi_signal_strength` | _(none)_ | Uses `device_class: SIGNAL_STRENGTH` |
| `energy_since_last_log` | _(none)_ | Uses `device_class: ENERGY` |
| `energy_total` | _(none)_ | Uses `device_class: ENERGY` |
| `sleep_mode_status` | `mdi:sleep` | ✅ Code resolved to name via `/api/sleep-modes` |
| `litres_filtered_internal` | `mdi:water-filter` | ✅ |
| `litres_filtered_external` | `mdi:water-filter` | ✅ |
| `days_filtered_internal` | `mdi:calendar-check` | ✅ |
| `days_filtered_external` | `mdi:calendar-check` | ✅ |

#### Numbers (`number.py`) — 10 entities

| Entity key | Icon | Notes |
|---|---|---|
| `boiling_temp` | `mdi:thermometer-high` | ✅ |
| `chilled_temp` | `mdi:thermometer-low` | ✅ |
| `boiling_duration` | `mdi:timer-outline` | ✅ |
| `chilled_duration` | `mdi:timer-outline` | ✅ |
| `sparkling_duration` | `mdi:timer-outline` | ✅ |
| `ambient_duration` | `mdi:timer-outline` | ✅ |
| `internal_filter_litres` | `mdi:water-filter` | ✅ |
| `internal_filter_days` | `mdi:calendar-clock` | ✅ |
| `external_filter_litres` | `mdi:water-filter` | ✅ |
| `external_filter_days` | `mdi:calendar-clock` | ✅ |

#### Switches (`switch.py`) — 20 entities

| Entity key | Icon | Notes |
|---|---|---|
| `safety_lock` | `mdi:lock` | ✅ Writable — PATCHes `safetyLockEnabled` |
| `hot_isolation` | `mdi:water-off` | ✅ Writable — PATCHes `hotIsolationEnabled` |
| All timer on/off switches (18) | `mdi:timer-play-outline` / `mdi:timer-stop-outline` | ✅ |

#### Binary Sensors (`binary_sensor.py`) — 1 entity

| Entity key | Icon | Notes |
|---|---|---|
| `system_fault` | _(none)_ | Uses `device_class: PROBLEM`. Read-only diagnostic. |

> **Note:** `safety_lock` and `hot_isolation` are **switches** (in `switch.py`), not binary sensors.
> They were removed from `binary_sensor.py` to avoid duplicate read-only entities.

#### Selects (`select.py`) — 3 entities

| Entity key | Icon | Notes |
|---|---|---|
| `sleep_mode` | `mdi:sleep` | ✅ |
| `energy_mode` | `mdi:power-plug` | ✅ |
| `sync_period` | `mdi:sync` | ✅ |

#### Times (`time.py`) — 18 entities

| Entity key | Icon | Notes |
|---|---|---|
| All on-time entities | `mdi:clock-start` | ✅ |
| All off-time entities | `mdi:clock-end` | ✅ |

## Data Shape Notes

### Hydrotap detail response (key fields):

**Important:** The detail endpoint (`/api/hydrotaps/{id}`) returns device metadata only —
it does NOT include `status`, `filterLifeRemaining*`, `averageDailyUsage`, or
`peakHourlyUsage`. Those fields come from the **list** endpoint
(`/api/owners/{ownerId}/hydrotaps`). The coordinator must merge both sources.

```json
{
  "hydrotapId": "uuid",
  "serialNumber": 2017102302086,
  "moduleName": "BC 100/75",
  "productNumber": "2824AU",
  "firmwareVersion": "B03.1.00 3.6 1.05",
  "calibrationDate": "2017-11-06",
  "50LitreFilterDate": "2017-12-14 00:00:00",
  "filterChangeDate": null,
  "externalBoosterInstalled": null,
  "macAddress": "58:7a:62:2e:8a:86",
  "connectionKey": null,
  "locationAlias": null,
  "retired": null,
  "previousHydrotapId": "",
  "hydrotapLocation": {
    "buildingName": "The Warehouse",
    "level": "1",
    "locationInBuilding": "Kitchen",
    "address": "165 Victoria St",
    "suburb": "Beaconsfield",
    "state": "New South Wales",
    "postcode": "2015",
    "country": "Australia"
  },
  "owner": { "ownerId": "uuid", "company": {...} },
  "ownerId": "uuid",
  "hydrotapGroups": [],
  "permissions": { "view": true, "edit": true },
  "createdAt": "2026-07-16T22:46:55+0000",
  "updatedAt": "2026-07-16T22:55:38+0000"
}
```

### Hydrotap list item (key fields — source of sensor data):

```json
{
  "hydrotapId": "uuid",
  "serialNumber": "2017102302086",
  "moduleName": "BC 100/75",
  "firmwareVersion": "B03.1.00 3.6 1.05",
  "calibrationDate": "2017-11-06T00:00:00.000Z",
  "status": "No alerts",
  "filterLifeRemainingLitres": 5984,
  "filterLifeRemainingDays": 350,
  "filterLifeRemainingEstimated": 350,
  "averageDailyUsage": 4.6,
  "peakHourlyUsage": 2.8,
  "lastSyncTimestamp": "2026-07-17T08:35:32+0000",
  "buildingName": "The Warehouse",
  "level": "1",
  "locationInBuilding": "Kitchen",
  "country": "Australia",
  "state": "New South Wales",
  "zipManaged": false,
  "connectionKey": null,
  "ownerCompanyName": "...",
  "facilityManagerCompanyName": null,
  "permissions": { "view": true, "edit": true },
  "hydrotapGroups": [],
  "groupName": null,
  "retired": null
}
```

### Settings response shape (verified live):

```json
{
  "hydrotapId": "uuid",
  "syncPeriod": "00:10:00",
  "sleepModeCode": 6,
  "safetyLockEnabled": true,
  "allowSafetySettingChange": true,
  "hotIsolationEnabled": false,
  "zipManaged": false,
  "language": "en",
  "lastUpdatedBy": "uuid",
  "lastUpdatedByType": "user",
  "zipViewPermission": true,
  "zipEditPermission": true,
  "createdAt": "2026-07-16T22:46:55+0000",
  "updatedAt": "2026-07-17T08:35:32+0000",
  "hydrotap": {
    "hydrotapId": "uuid",
    "macAddress": "58:7a:62:2e:8a:86",
    "connectionKey": null,
    "hydrotapLocationId": "uuid",
    "ownerId": "uuid",
    "serialNumber": 2017102302086,
    "productNumber": "2824AU",
    "moduleName": "BC 100/75",
    "firmwareVersion": "B03.1.00 3.6 1.05",
    "locationAlias": null,
    "calibrationDate": "2017-11-06",
    "filterChangeDate": null,
    "50LitreFilterDate": "2017-12-14 00:00:00",
    "externalBoosterInstalled": null,
    "retired": null,
    "previousHydrotapId": "",
    "createdAt": "...",
    "updatedAt": "...",
    "permissions": { "view": true, "edit": true }
  },
  "externalFilterLimits": { "days": null, "litres": null },
  "internalFilterLimits": { "days": 360, "litres": 6000 },
  "boiling": { "temp": 98, "duration": 15, "isFeature": true },
  "chilled": { "temp": 5, "duration": 15, "isFeature": true },
  "sparkling": { "temp": null, "duration": 15, "isFeature": false },
  "ambient": { "duration": 15, "isFeature": false },
  "security": {
    "pin": { "enabled": false, "value": null },
    "hydrotapCanModify": true
  },
  "energy": {
    "activeMode": "everyday",
    "daily": {
      "mon": { "onTimeActive": false, "onTime": "07:00:00", "offTimeActive": false, "offTime": "18:00:00" },
      "tue": { "onTimeActive": false, "onTime": "07:00:00", "offTimeActive": false, "offTime": "18:00:00" },
      "wed": { "onTimeActive": false, "onTime": "07:00:00", "offTimeActive": false, "offTime": "18:00:00" },
      "thu": { "onTimeActive": false, "onTime": "07:00:00", "offTimeActive": false, "offTime": "18:00:00" },
      "fri": { "onTimeActive": false, "onTime": "07:00:00", "offTimeActive": false, "offTime": "18:00:00" },
      "sat": { "onTimeActive": false, "onTime": "07:00:00", "offTimeActive": false, "offTime": "18:00:00" },
      "sun": { "onTimeActive": false, "onTime": "07:00:00", "offTimeActive": false, "offTime": "18:00:00" }
    },
    "everyday": { "onTimeActive": false, "onTime": "07:00:00", "offTimeActive": true, "offTime": "19:00:00" },
    "weekdayWeekend": {
      "weekday": { "onTimeActive": false, "onTime": "07:00:00", "offTimeActive": false, "offTime": "18:00:00" },
      "weekend": { "onTimeActive": false, "onTime": "07:00:00", "offTimeActive": false, "offTime": "18:00:00" }
    }
  }
}
```

Key corrections from earlier assumptions:
- `boiling`/`chilled`/`sparkling` have `duration` as an **integer** (seconds), not `{onTime, offTime}`
- `ambient` has no `temp` field (ambient is not temperature-controlled)
- `sparkling.temp` is `null` when the feature is not available (`isFeature: false`)
- `sleepModeCode` is an **integer** (6), not a string
- `security` is `{ pin: { enabled, value }, hydrotapCanModify }`, not `{ pinEnabled }`
- `energy` has an `activeMode` field ("everyday" | "daily" | "weekdayWeekend")
- `syncPeriod` is `"00:10:00"` (10 min), not `"03:00:00"`

### Settings-options response shape (verified live):

```json
{
  "water": {
    "ambient": false,
    "boiling": {
      "temp": { "min": 68, "max": 100, "step": 0.5 },
      "duration": { "min": 5, "max": 15, "step": 1 }
    },
    "chilled": {
      "temp": { "min": 5, "max": 9, "step": 1, "range": 4 },
      "duration": { "min": 5, "max": 15, "step": 1 }
    },
    "sparkling": false
  },
  "filters": {
    "internal": {
      "litres": { "default": 6000, "min": 500, "max": 10000, "step": 500 },
      "days": { "default": 360, "min": 30, "max": 420, "step": 30 }
    },
    "external": {
      "litres": { "default": 6000, "min": 500, "max": 10000, "step": 500 },
      "days": { "default": 360, "min": 30, "max": 420, "step": 30 }
    }
  },
  "safety": {
    "safetyLockEnabled": true,
    "hotIsolationEnabled": true,
    "allowSafetySettingChange": true
  },
  "syncPeriod": { "min": "00:10:00", "max": "01:00:00", "step": "00:10:00" }
}
```

Key observations:
- `water.ambient` and `water.sparkling` are `false` — no settings available for those types
- Boiling temp range: 68–100°C, step 0.5
- Chilled temp range: 5–9°C, step 1 (with `range: 4` indicating 4°C adjustable span)
- Filter limits: litres 500–10000 (step 500), days 30–420 (step 30)
- `safety` lists which safety toggles are **available** (not their current state)
- Sync period: 10–60 min, step 10 min

### Status log shape:
```json
{
  "hydrotapLogId": "uuid",
  "hydrotapId": "uuid",
  "timestamp": "2026-07-17T08:35:32+0000",
  "createdAt": "2026-07-17T08:35:32+0000",
  "timeSinceLastLog": "00:10:00",
  "energyKwhSinceLastLog": 0.5,
  "energyKwhTotal": 1234.5,
  "daysFilteredInternal": 15,
  "litresFilteredInternal": 200,
  "daysFilteredExternal": 0,
  "litresFilteredExternal": 0,
  "sleepModeStatus": "active",
  "wifiSignalStrength": -55,
  "hydrotapActive": true
}
```

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
├── exploration/
│   └── explore.py               # Live API exploration script
├── tests/
│   ├── __init__.py
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
