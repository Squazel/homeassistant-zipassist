# TODO

Incomplete work items from the original implementation plan.

## Bugs

| Area | Details |
|---|---|
| ~~Energy entities disappear on mode change~~ | ✅ Fixed — `switch.py` and `time.py` `async_setup_entry` no longer gate energy entities on `activeMode`. All energy switches and times are always created. |
| ~~WeekdayWeekend entities exist but invisible~~ | ✅ Fixed — same fix as above. Weekday/weekend switches and times now always appear. |
| Daily (i.e. individual Sun-Sat) controls are missing from the dashboard | |
| "Sleep Mode" shows a value from 0..6, but should have text descriptions exposed to the user (see official UI for mappings) | |
| "Sleep Mode" and "Sleep Mode Status" - potential confusion with similarly-named entities | |

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

## Dashboards / Cards

Ship standard Lovelace dashboards as part of the HACS package to mirror the ZipAssist official website layout.

### Goals
- Provide a familiar UI for users transitioning from the ZipAssist website
- Roughly mirror the website's layout and control groupings (not pixel-perfect)
- Later iterations can introduce more modern or HA-native appearances

### Design decisions
- **Dashboard generator**: A Python script (`tools/generate_dashboards.py`) queries the Home Assistant REST API to auto-discover all zipassist entities, groups them by device, and emits ready-to-use dashboard YAML — no manual entity ID mapping needed
- **Generator located at** `tools/generate_dashboards.py`; documented in `custom_components/zipassist/dashboards/README.md`
- **Section layout** mirrors the website's HydroTap detail page: Info & Status, Filter Life, Usage, Safety & Security, Temperature, Dispense, Filter Limits, On/Off Timers, Sleep Mode

### Implementation status
1. ~~**Research**: Open the ZipAssist website in browser, analyze layout sections and control groupings~~ ✅
2. ~~**Design**: Map website sections to HA card types~~ ✅
3. ~~**Build**: Create the dashboard generator script~~ ✅
4. ~~**Integrate**: Custom card ships with the integration (static path + add_extra_js_url)~~ ✅
5. ~~**Document**: Add dashboard/card setup instructions to docs/~~ ✅

## Card styling (match official ZipAssist HydroTap page)

**Status:** ✅ Complete — `zipassist-card.js` rewritten with official ZipAssist look.  
**Version:** keep `manifest.json` / `pyproject.toml` in sync; bump both when changing the card JS (cache bust).  
**Source of truth:** Owner HydroTap management page on https://zipassist.zipindustries.com (e.g. `/owner/management/{hydrotapId}`).  
**File to change:** `custom_components/zipassist/frontend/zipassist-card.js` (and bump `manifest.json` version for cache bust).  
**Goal:** Familiar ZipAssist look inside HA — full-width expandable sections, red heading bars, site-like controls for entities we already expose. Not pixel-perfect; match structure, hierarchy, and control language.

### Official layout (observed live)

Page structure top → bottom:

1. **Device header / identity block** (not a red panel)
   - Left column: building name, address, level/location, group(s), timezone (icon + label + value).
   - Right column (grey panel): serial, module name, product number, calibration date, firmware, first 50L filtered date.
   - HA mapping today: status sensors we have (serial, firmware, last sync, status, wifi, sleep mode status, filter remaining, etc.). Product/address/group may be missing entities — show only what exists; leave gaps for future entities.

2. **Stacked full-width collapsible panels** (main UI pattern)
   Official section order / titles (uppercase on site):

   | Official panel | SHOW/HIDE | HA entities to bind (existing keys) | Notes |
   |---|---|---|---|
   | SECURITY SETTINGS | yes | *(PIN / allow security change not exposed yet)* | Skip or stub until entities exist |
   | SAFETY SETTINGS | yes | `safety_lock`, `hot_isolation` (+ future allow-safety-change) | YES/NO style toggles |
   | SYNC TIME | yes | `sync_period` (number) | Site uses time-of-day fields; we only have period — use number control |
   | ZIP PERMISSIONS | yes | *(not exposed)* | Skip until entities exist |
   | SYSTEM FAULT ALERTS | yes | `system_fault`, `system_fault_details` | Read-only / status |
   | FILTERS | yes | filter life sensors + `internal_filter_*` / `external_filter_*` limits | Mix of readouts + number limits + enable-style if we add later |
   | DISPENSE SETTINGS | yes | `boiling_duration`, `chilled_duration`, `sparkling_duration`, `ambient_duration` | Number steppers |
   | TEMPERATURE SETTINGS | yes | `boiling_temp`, `chilled_temp` | Number steppers (°C) |
   | ON/OFF TIMERS | yes | `energy_mode` + everyday/weekday/weekend/daily `*_active` switches + `*_time` times | **Must nest modes** — see On/Off Timers structure below |
   | SLEEP MODE | yes | `sleep_mode` select (+ `sleep_mode_status` read-only) | Dropdown / select |
   | LOGS / GRAPH | yes | *(API not wired to card)* | Out of scope until coordinator exposes data |

3. **Collapse behaviour**
   - Each panel has a **full-width header bar** with title left and **SHOW / HIDE** control right (chevron + text).
   - Expanded: white body under the bar with padded rows.
   - Collapsed: only the red bar visible (no body).
   - Multiple panels can be open at once (site allows this).
   - Default: match site bias — identity open; most settings collapsed except one or two (e.g. safety + faults) **or** collapse all except Info — pick one and document.

### Visual system (measured from site)

| Token | Official value | Card implementation guidance |
|---|---|---|
| Section bar background | `rgb(230, 24, 55)` ≈ `#E61837` | Solid red first; optional subtle texture later (`watercolour-bg.jpg` is site-specific — do **not** hotlink Zip CDN in production card; optional local asset only if licensed) |
| Section bar text | White `#FFFFFF` | Title uppercase, ~14–16px, semi-bold/bold |
| Section bar height | ~40px | `padding: 10px 15px`; full card width |
| Section bar width | 100% of content column | Card content should be **full width of `ha-card`** (no narrow centered column) |
| Toggle ON | Green `rgb(40, 182, 44)` ≈ `#28B62C`, white bold label | Segmented control: green half + empty half, labels **YES** / **ENABLED** as appropriate |
| Toggle OFF | Red `#E61837` (or site DISABLED red block) + white text | **NO** / **DISABLED** |
| Toggle shape | Rectangular, **no** large border-radius (site ~0) | Prefer flat Zip-style pills over Material round `ha-switch` *or* style a custom dual-state control |
| Body background | White | `#fff` / `var(--card-background-color)` with white preference in light mode |
| Page chrome | Light grey page bg | Rely on HA dashboard background; card outer may be borderless or light grey |
| Row layout | Label left (~40%), control right | Min row height ~48–56px; generous vertical padding; divider optional/light |
| Typography | Clean sans; labels dark grey, not tiny uppercase chips | Avoid current “tiny uppercase section + dense tiles” look for settings panels |

### Control mapping (by entity domain / key)

Implement **appropriate controls** for entities we already have — not plain text for everything.

| Domain / keys | Official control language | Card control |
|---|---|---|
| `switch.*` safety (`safety_lock`, `hot_isolation`) | Green **YES** / red **NO** (or ENABLED/DISABLED) segmented toggle | Custom Zip toggle calling `switch.turn_on` / `turn_off` |
| `switch.*` energy `*_active` | Same binary enable style | Same Zip toggle |
| `number` temps (`boiling_temp`, `chilled_temp`) | Numeric field / stepper with unit | Number input or − / value / + ; show °C; clamp min/max from entity attributes |
| `number` durations (`*_duration`) | Numeric | Number input; show seconds (or site unit if known) |
| `number` filter limits (`internal_filter_litres`, etc.) | Numeric with range hints | Number input; show L or days |
| `number` `sync_period` | Site uses clock UI; we have period | Number input + unit label (minutes/hours per entity) |
| `select` `sleep_mode`, `energy_mode` | Dropdown | `<select>` or HA-like select; options from `attributes.options` |
| `time` `*_time` | Time entry | `<input type="time">` → `time.set_value` |
| `sensor` / `binary_sensor` status, filter remaining, energy, wifi, serial, firmware, faults | Read-only text in identity or fault panel | Read-only row: label + value (+ unit); fault binary as status badge |
| More-info | Site has ? help | Keep small info affordance opening `hass-more-info` without cluttering Zip look |

### Section → entity wiring (rewrite SECTIONS config)

Replace generic “Info tiles + mixed rows” with **site-ordered panels**:

1. **Device info** (static block, not red bar — or single non-collapsible header card area)  
   Sensors: `status`, `serial_number`, `firmware_version`, `last_sync`, `wifi_signal_strength`, `sleep_mode_status`, filter remaining trio, usage/energy readouts as secondary facts.
2. **Safety settings** — `safety_lock`, `hot_isolation`
3. **Sync time** — `sync_period`
4. **System fault alerts** — `system_fault`, `system_fault_details`
5. **Filters** — remaining sensors + internal/external limit numbers (group internal vs external sub-blocks like site)
6. **Dispense settings** — duration numbers
7. **Temperature settings** — temp numbers
8. **On/off timers** — see **On/Off Timers structure** (required nesting)
9. **Sleep mode** — `sleep_mode` select

Skip empty panels (no available entities).

### On/Off Timers structure (required)

Official ZipAssist keeps the three energy-timer **modes** visually separate so the panel is not one long flat list. The HA card **must** do the same.

**Modes (three buckets):**

| Mode (UI label) | `energy_mode` value(s) to treat as active | Entities |
|---|---|---|
| **Everyday** | Everyday / equivalent option string from select | `energy_everyday_on_active`, `energy_everyday_on_time`, `energy_everyday_off_active`, `energy_everyday_off_time` |
| **Weekday / Weekend** | WeekdayWeekend / equivalent | Weekday on/off active+time **and** weekend on/off active+time (two sub-groups under this mode) |
| **Daily** | Daily / equivalent | Per-day Mon–Sun: `energy_daily_{mon..sun}_on_active`, `_on_time`, `_off_active`, `_off_time` |

**Required UX (pick one primary pattern; both are acceptable):**

1. **Nested tabs (preferred if space allows)**  
   - Outer panel: red bar **ON/OFF TIMERS** + SHOW/HIDE (same as other sections).  
   - Inside expanded body, top row: **`energy_mode` select** (Active Mode).  
   - Below that: **three tabs** — `Everyday` | `Weekday / Weekend` | `Daily`.  
   - Only the selected tab’s controls are visible.  
   - Optional: when user changes `energy_mode`, auto-switch to the matching tab.

2. **Separate expanders (alt`energy_mode` + **three nested tabs or three nested expanders** (Everyday / Weekday–Weekend / Daily) — never a single flat list of all timer entities.
7. **Manual compare** against official page screenshots (security/safety/filters/temp/timers nesting
   - Inside: `energy_mode` select at top.  
   - Then **three nested collapsible sub-panels** (not full red site bars — secondary style, e.g. grey/light bar or indented Zip sub-headers):  
     - Everyday  
     - Weekday / Weekend (with clear Weekday vs Weekend row groups)  
     - Daily (list Mon–Sun; each day on/off active + times)  
   - Sub-panels independently expand/collapse; default open the sub-panel that matches current `energy_mode`.

**Row content inside each mode:**

- Each timer line: label (e.g. “On”, “Off”, or “Monday — On”) + **Zip toggle** for `*_active` + **time input** for `*_time` on the same row or tight pair of rows (match site density where possible).
- Do **not** dump all everyday + weekday + weekend + 7× daily entities into one undifferentiated list.
- If a mode’s entities are missing, hide that tab/expander entirely.

**Acceptance (timers-specific):**

- [ ] User never sees all three modes’ controls in one flat scrolling list.
- [ ] Everyday / Weekday-Weekend / Daily are clearly separated via tabs **or** nested expanders.
- [ ] `energy_mode` remains visible and editable at the top of the timers panel.
- [ ] Daily mode is scannable by weekday without mixing in Everyday/Weekend rows.

### UX / interaction requirements

- [ ] Full-width panels inside `ha-card` (edge-to-edge bars).
- [ ] Red bar headers + SHOW/HIDE (or chevron + HIDE/SHOW text) matching site semantics.
- [ ] Collapsed state hides body completely.
- [ ] Expanded state: white body, label/control rows, not dense info-tiles for settings.
- [ ] Zip-style binary toggles for switches (not default round Material switch as primary look).
- [ ] Numbers/selects/times editable inline with service calls (already partially done — restyle).
- [ ] Read-only sensors not pretending to be inputs.
- [ ] Dark mode: keep red bars; body use HA card background; toggles keep green/red semantics.
- [ ] Accessibility: real `<button>` headers, `aria-expanded`, keyboard toggle, focus styles.
- [ ] Do not break picker (`preview: false`, never-throw `getStubConfig`).
- [ ] Bump integration version after JS change for cache bust.

### Implementation plan

1. **Restyle CSS** in card shadow DOM: panel heading, body, rows, Zip toggle, inputs.
2. **Restructure SECTIONS** to official names/order and panel types (`info` block vs `settings` rows).
3. **ZipToggle component** (inline in card JS): two-segment control bound to switch entities.
4. **Row renderers** by domain: `renderSwitchRow`, `renderNumberRow`, `renderSelectRow`, `renderTimeRow`, `renderSensorRow`.
5. **Filters panel layout**: two sub-groups Internal / External.
6. **Timers panel layout**: mode select + conditional groups.
7. **Manual compare** against official page screenshots (security/safety/filters/temp/timers).
8. **HA check** on Kitchen dashboard card after deploy.

### Out of scope (for this styling pass)

- PIN / Zip permissions / graphs / logs (need new entities or API wiring — already listed under Not Started).
- Pixel-perfect watercolour texture unless we vendor a licensed local asset.

### Acceptance criteria

- [ ] User glancing at HA card recognizes ZipAssist section pattern (red full-width bars + SHOW/HIDE).
- [ ] Safety switches use green/red YES/NO (or ENABLED/DISABLED) controls.
- [ ] Temps, durations, filter limits, sync period use clear numeric controls.
- [ ] Sleep/energy mode use selects; timer times use time inputs; timer actives use Zip toggles.
- [ ] No empty header-only card when entities exist (regression).
- [ ] Works in light and dark HA themes without unreadable contrast.
