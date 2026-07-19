# TODO

Incomplete work items from the original implementation plan.

## Bugs

| Area | Details |
|---|---|
| ~~Energy entities disappear on mode change~~ | ✅ Fixed — `switch.py` and `time.py` `async_setup_entry` no longer gate energy entities on `activeMode`. All energy switches and times are always created. |
| ~~WeekdayWeekend entities exist but invisible~~ | ✅ Fixed — same fix as above. Weekday/weekend switches and times now always appear. |

## Not Started

| Area | Details |
|---|---|
| PIN settings entity | `security.pin` in settings not exposed |
| Language select | `language` field in settings not exposed |
| Allow safety setting change | `allowSafetySettingChange` toggle not exposed |
| Zip managed indicator | `zipManaged` flag from hydrotap detail not exposed as entity |
| Usage graphs in HA | API methods exist (`get_usage_graph`, `get_average_usage_graph`) but no HA sensors/entities consume them |
| Notes read/write | API methods exist (`get_notes`, `add_note`) but no HA entities consume them |

## API Endpoints Not Consumed by Coordinator

These client methods exist but the coordinator never calls them, so the data is never available to entities:

| Endpoint | Client Method | Potential Use |
|---|---|---|
| `/api/hydrotaps/{id}/logs/filter-usage` | `get_filter_usage()` | Filter change history sensor |
| `/api/hydrotaps/{id}/logs/dispense-events` | `get_dispense_events()` | Dispense count/type sensors |
| `/api/hydrotaps/{id}/logs/daily-usage` | `get_daily_usage()` | Daily water/energy usage sensors |
| `/api/hydrotaps/{id}/usage/water` | `get_water_usage()` | Water usage history (requires date range) |
| `/api/hydrotaps/{id}/usage/energy` | `get_energy_usage()` | Energy usage history (requires date range) |
| `/api/hydrotaps/{id}/graphs/usage` | `get_usage_graph()` | Graph series for HA charts |
| `/api/hydrotaps/{id}/graphs/average-usage` | `get_average_usage_graph()` | Average usage graph data |
| `/api/hydrotaps/{id}/notes` | `get_notes()` / `add_note()` | Notes display/entry |
| `/api/hydrotaps/{id}/timezone` | `get_timezone()` | Timezone sensor (diagnostic) |
| `/api/system-faults` | `get_system_faults()` | Fault code lookup table |
| `/api/system-events` | `get_system_events()` | Event code lookup table |
| `/api/countries` | `get_countries()` | Country reference data |
| `/api/timezones` | `get_timezones()` | Timezone reference data |
| `/api/hydrotap-search-options` | `get_hydrotap_search_options()` | Admin search metadata |
| `/api/owners/{ownerId}/hydrotap-groups` | `get_owner_hydrotap_groups()` | Group membership sensor |
| `/api/owners/{ownerId}/hydrotap-system-faults/major` | `get_owner_faults_major()` | Owner fault dashboard |
| `/api/owners/{ownerId}/hydrotap-system-faults/minor` | `get_owner_faults_minor()` | Owner alert dashboard |
| `/api/owners/{ownerId}/hydrotaps-without-system-faults` | `get_owner_hydrotaps_no_faults()` | Healthy tap count |

## Pending

| Area | Details |
|---|---|
| HACS submission | `hacs.json` exists but not yet submitted |
| Tests | Unit tests exist for client, config_flow, coordinator, helpers, services — could be expanded |