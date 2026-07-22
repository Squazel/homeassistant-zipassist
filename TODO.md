# TODO

Remaining work items for the ZipAssist CMMS integration.

## Bugs

| Area | Details |
|---|---|
| "Sleep Mode" and "Sleep Mode Status" — potential confusion with similarly-named entities | The `sleep_mode` select and `sleep_mode_status` sensor have very similar names. Consider renaming for clarity. |

## Not Started

| Area | Details |
|---|---|
| PIN settings entity | `security.pin` in settings not exposed |
| Language select | `language` field in settings not exposed |
| Allow safety setting change | `allowSafetySettingChange` toggle not exposed |
| Zip managed indicator | `zipManaged` flag from hydrotap detail not exposed as entity |
| Usage graphs in HA | API methods exist (`get_usage_graph`, `get_average_usage_graph`) but no HA sensors/entities consume them |
| Notes read/write | API methods exist (`get_notes`, `add_note`) but no HA entities consume them |
| Temperature sliders | `boiling_temp` and `chilled_temp` are `number` entities with textbox/up-down controls. Change to sliders over their respective ranges while keeping the value visible (textbox + up/down still available alongside the slider). |
| On/Off Timer row merging | Each day/group has separate "On Active" + "On Time" rows (and "Off Active" + "Off Time"). Merge each pair into a single row: "On … Yes/No … Time entry" and "Off … Yes/No … Time entry". Total of 10 On + 10 Off rows expected. Do not change general styling or control implementation, or the entities themselves. |
| Sleep Mode text descriptors | `sleep_mode` select currently shows raw numbers 0–6. Replace with descriptive text labels (numbers still used behind the scenes for the API). Options: Disabled, 2 Hours → 68°C, 2 Hours → Off, Lux Sensor → 68°C, Lux Sensor → Off, Lux Sensor or 2 Hours → 68°C, Lux Sensor or 2 Hours → Off. |
| Change Yes/No buttons in the On/Off Timers section to Enabled (green) / Disabled [rgb(85,85,85) text on rgb(227,227,227)] toggle buttons (not switches) to match official interface | |

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
