# API Endpoints

All known ZipAssist CMMS API endpoints. All paths are prefixed with `/api`.

> **Validation:** Run `python exploration/explore.py --endpoints-only` to verify this list against the live API.

## Authentication

**Flow:** HTTP Basic → JWT Bearer

1. `GET /api/auth/jwt/login` with header `Authorization: Basic <base64(email:password)>`
2. Response: `{ "token": "<jwt>", "user": { "name": "...", "userType": "owner|admin|facilityManager", ... } }`
3. All subsequent requests: header `Authorization: Bearer <token>`
4. Refresh: `GET /api/auth/jwt/refresh` (returns new token when near expiry)

## Hydrotap Listing

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

## Hydrotap Detail & Settings

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/hydrotaps/{id}` | Hydrotap detail (location, serial, firmware, status, filter life, etc.) |
| GET | `/api/hydrotaps/{id}/settings` | Current settings (temperature, dispense, filters, energy, safety, etc.) |
| GET | `/api/hydrotaps/{id}/settings-options` | Allowed ranges/options for each setting |
| PATCH | `/api/hydrotaps/{id}/settings` | Write settings — body is the same shape as GET settings |
| GET | `/api/hydrotaps/{id}/timezone` | Returns `{ "timezone": "Australia/Sydney" }` |

## Logs & Usage

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

## Faults & Alerts

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/system-faults` | Fault code definitions |
| GET | `/api/system-events` | System event definitions |
| PATCH | `/api/hydrotaps/{id}/system-faults/{faultId}` | Clear a fault (body: `{"endTimestamp": "..."}`) |

## Hydrotap Search (Admin)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/hydrotaps?perPage=10&page=0&search=<base64json>` | Search all hydrotaps |
| GET | `/api/hydrotap-search-options` | Filter option metadata |

## Owner-specific Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/owners/{ownerId}/hydrotaps` | List owner's hydrotaps |
| GET | `/api/owners/{ownerId}/hydrotap-groups` | Owner's groups |
| GET | `/api/owners/{ownerId}/hydrotap-system-faults/major` | Fault dashboard data |
| GET | `/api/owners/{ownerId}/hydrotap-system-faults/minor` | Alert dashboard data |
| GET | `/api/owners/{ownerId}/hydrotaps-without-system-faults` | Nominal taps |

## Other

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/sleep-modes/{id}` | Available sleep mode options |
| GET | `/api/countries` | Country list |
| GET | `/api/timezones` | Timezone list |
| GET | `/api/hydrotaps/{id}/notes` | Admin notes for a tap |
| POST | `/api/hydrotaps/{id}/notes` | Add a note |

## Data Shapes

### Hydrotap Detail Response

**Important:** The detail endpoint (`/api/hydrotaps/{id}`) returns device metadata only —
it does NOT include `status`, `filterLifeRemaining*`, `averageDailyUsage`, or
`peakHourlyUsage`. Those fields come from the **list** endpoint
(`/api/owners/{ownerId}/hydrotaps`). The coordinator must merge both sources.

```json
{
  "hydrotapId": "uuid",
  "serialNumber": 1000000000001,
  "moduleName": "BC 100/75",
  "productNumber": "0000XX",
  "firmwareVersion": "B03.1.00 3.6 1.05",
  "calibrationDate": "2020-01-01",
  "50LitreFilterDate": "2020-02-01 00:00:00",
  "filterChangeDate": null,
  "externalBoosterInstalled": null,
  "macAddress": "00:00:00:00:00:01",
  "connectionKey": null,
  "locationAlias": null,
  "retired": null,
  "previousHydrotapId": "",
  "hydrotapLocation": {
    "buildingName": "My Office",
    "level": "1",
    "locationInBuilding": "Kitchen",
    "address": "123 Example St",
    "suburb": "Exampleville",
    "state": "New South Wales",
    "postcode": "2000",
    "country": "Australia"
  },
  "owner": { "ownerId": "uuid", "company": {} },
  "ownerId": "uuid",
  "hydrotapGroups": [],
  "permissions": { "view": true, "edit": true },
  "createdAt": "2026-07-16T22:46:55+0000",
  "updatedAt": "2026-07-16T22:55:38+0000"
}
```

### Hydrotap List Item (source of sensor data)

```json
{
  "hydrotapId": "uuid",
  "serialNumber": "1000000000001",
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
  "buildingName": "My Office",
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

### Settings Response

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
    "macAddress": "00:00:00:00:00:01",
    "connectionKey": null,
    "hydrotapLocationId": "uuid",
    "ownerId": "uuid",
    "serialNumber": 1000000000001,
    "productNumber": "0000XX",
    "moduleName": "BC 100/75",
    "firmwareVersion": "B03.1.00 3.6 1.05",
    "locationAlias": null,
    "calibrationDate": "2020-01-01",
    "filterChangeDate": null,
    "50LitreFilterDate": "2020-02-01 00:00:00",
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

Key details:
- `boiling`/`chilled`/`sparkling` have `duration` as an **integer** (seconds), not `{onTime, offTime}`
- `ambient` has no `temp` field (ambient is not temperature-controlled)
- `sparkling.temp` is `null` when the feature is not available (`isFeature: false`)
- `sleepModeCode` is an **integer**, not a string
- `security` is `{ pin: { enabled, value }, hydrotapCanModify }`, not `{ pinEnabled }`
- `energy` has an `activeMode` field ("everyday" | "daily" | "weekdayWeekend")
- `syncPeriod` is `"00:10:00"` (10 min)

### Settings-Options Response

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

### Status Log

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