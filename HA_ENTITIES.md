# HA devices in YAML-like pseudocode for Home Assistant

## Device naming convention

- **Device name:** `{buildingName} - {level}/{location}` e.g. `The Warehouse - 1/Kitchen`
- **Model** (`moduleName`) is stored as device `model` metadata, e.g. `BC 100/75`
- The generic "HydroTap" label from the API is discarded

## Device example

device:
  identifiers: zipassist_631a3385-301b-4c9c-97ed-3a1a50061f5c
  name: "The Warehouse - 1/Kitchen"
  manufacturer: "Zip Industries"
  model: "BC 100/75"
  sw_version: "B03.1.00 3.6 1.05"
  serial_number: "2017102302086"

Note: `moduleName` (e.g. "BC 100/75") is stored in the `model` field of the HA device
registry. The API's internal name/label (e.g. "HydroTap - BC 100/75") is stored as
a `configuration_url`-type note or extra attribute, not used as the primary name.

# --- read-only sensors (from hydrotap detail / latest status log) ---

sensor:
  - name: "The Warehouse - 1/Kitchen Filter Litres Remaining"
    unique_id: zipassist_631a3385_filter_litres
    state: 5984
    unit_of_measurement: "L"
    icon: mdi:water-filter

  - name: "The Warehouse - 1/Kitchen Filter Days Remaining"
    unique_id: zipassist_631a3385_filter_days
    state: 350
    unit_of_measurement: "days"
    icon: mdi:calendar-clock

  - name: "The Warehouse - 1/Kitchen Filter Estimated Days"
    unique_id: zipassist_631a3385_filter_estimated
    state: 350
    unit_of_measurement: "days"
    icon: mdi:calendar-check

  - name: "The Warehouse - 1/Kitchen Average Daily Usage"
    unique_id: zipassist_631a3385_daily_usage
    state: 4.6
    unit_of_measurement: "L/day"
    icon: mdi:water

  - name: "The Warehouse - 1/Kitchen Peak Hourly Usage"
    unique_id: zipassist_631a3385_peak_usage
    state: 2.8
    unit_of_measurement: "L/h"
    icon: mdi:water-pump

  - name: "The Warehouse - 1/Kitchen Last Sync"
    unique_id: zipassist_631a3385_last_sync
    device_class: timestamp
    icon: mdi:cloud-sync

  - name: "The Warehouse - 1/Kitchen Status"
    unique_id: zipassist_631a3385_status
    icon: mdi:alert-circle-check

  - name: "The Warehouse - 1/Kitchen Serial Number"
    unique_id: zipassist_631a3385_serial
    icon: mdi:numeric

  - name: "The Warehouse - 1/Kitchen Firmware Version"
    unique_id: zipassist_631a3385_firmware
    icon: mdi:chip

# --- settings as number entities (read/write) ---

number:
  - name: "The Warehouse - 1/Kitchen Boiling Temperature"
    unique_id: zipassist_631a3385_boiling_temp
    native_min_value: 68
    native_max_value: 100
    native_step: 0.5
    native_unit_of_measurement: "°C"

  - name: "The Warehouse - 1/Kitchen Chilled Temperature"
    unique_id: zipassist_631a3385_chilled_temp
    native_min_value: 5
    native_max_value: 9
    native_step: 1
    native_unit_of_measurement: "°C"

# --- binary sensors ---

binary_sensor:
  - name: "The Warehouse - 1/Kitchen Safety Lock"
    unique_id: zipassist_631a3385_safety_lock
    icon: mdi:lock

  - name: "The Warehouse - 1/Kitchen Hot Isolation"
    unique_id: zipassist_631a3385_hot_isolation
    icon: mdi:water-off

# --- switches (read/write) ---

switch:
  - name: "The Warehouse - 1/Kitchen Safety Lock"
    unique_id: zipassist_631a3385_safety_lock
    icon: mdi:lock
    note: "Toggle safety lock on/off. Only available if safetyLockEnabled is true in settings-options."

  - name: "The Warehouse - 1/Kitchen Hot Isolation"
    unique_id: zipassist_631a3385_hot_isolation
    icon: mdi:water-off
    note: "Toggle hot isolation on/off. Only available if hotIsolationEnabled is true in settings-options."

  # Energy timer active toggles — conditionally created based on activeMode
  - name: "The Warehouse - 1/Kitchen Energy Everyday On Active"
    unique_id: zipassist_631a3385_energy_everyday_on_active
    icon: mdi:timer-play-outline
    note: "Only available when energy.activeMode == 'everyday'"

  - name: "The Warehouse - 1/Kitchen Energy Everyday Off Active"
    unique_id: zipassist_631a3385_energy_everyday_off_active
    icon: mdi:timer-stop-outline
    note: "Only available when energy.activeMode == 'everyday'"

  # Daily schedule switches (mon–sun) — only when activeMode == 'daily'
  - name: "The Warehouse - 1/Kitchen Energy Monday On Active"
    unique_id: zipassist_631a3385_energy_daily_mon_on_active
    icon: mdi:timer-play-outline

  - name: "The Warehouse - 1/Kitchen Energy Monday Off Active"
    unique_id: zipassist_631a3385_energy_daily_mon_off_active
    icon: mdi:timer-stop-outline

  # ... (tue–sun follow the same pattern)

  # Weekday/weekend switches — only when activeMode == 'weekdayWeekend'
  - name: "The Warehouse - 1/Kitchen Energy Weekday On Active"
    unique_id: zipassist_631a3385_energy_weekday_on_active
    icon: mdi:timer-play-outline

  - name: "The Warehouse - 1/Kitchen Energy Weekday Off Active"
    unique_id: zipassist_631a3385_energy_weekday_off_active
    icon: mdi:timer-stop-outline

  - name: "The Warehouse - 1/Kitchen Energy Weekend On Active"
    unique_id: zipassist_631a3385_energy_weekend_on_active
    icon: mdi:timer-play-outline

  - name: "The Warehouse - 1/Kitchen Energy Weekend Off Active"
    unique_id: zipassist_631a3385_energy_weekend_off_active
    icon: mdi:timer-stop-outline

# --- select entities (read/write) ---

select:
  - name: "The Warehouse - 1/Kitchen Sleep Mode"
    unique_id: zipassist_631a3385_sleep_mode
    icon: mdi:sleep
    options: ["0", "1", "2", "3", "4", "5", "6", "7", "8"]
    note: "Options are fetched from /api/sleep-modes when available; falls back to codes 0–8."

  - name: "The Warehouse - 1/Kitchen Energy Mode"
    unique_id: zipassist_631a3385_energy_mode
    icon: mdi:power-plug
    options: ["everyday", "daily", "weekdayWeekend"]
    note: "Changing this will show/hide the corresponding switch and time entities."

  - name: "The Warehouse - 1/Kitchen Sync Period"
    unique_id: zipassist_631a3385_sync_period
    icon: mdi:sync
    options: ["00:10:00", "00:20:00", "00:30:00", "00:40:00", "00:50:00", "01:00:00"]
    note: "How often the hydrotap syncs with the cloud. Range: 10–60 minutes."

# --- time entities (read/write) ---

time:
  - name: "The Warehouse - 1/Kitchen Energy Everyday On Time"
    unique_id: zipassist_631a3385_energy_everyday_on_time
    icon: mdi:clock-start
    note: "Only available when energy.activeMode == 'everyday'"

  - name: "The Warehouse - 1/Kitchen Energy Everyday Off Time"
    unique_id: zipassist_631a3385_energy_everyday_off_time
    icon: mdi:clock-end
    note: "Only available when energy.activeMode == 'everyday'"

  # Daily schedule times (mon–sun) — only when activeMode == 'daily'
  - name: "The Warehouse - 1/Kitchen Energy Monday On Time"
    unique_id: zipassist_631a3385_energy_daily_mon_on_time
    icon: mdi:clock-start

  - name: "The Warehouse - 1/Kitchen Energy Monday Off Time"
    unique_id: zipassist_631a3385_energy_daily_mon_off_time
    icon: mdi:clock-end

  # ... (tue–sun follow the same pattern)

  # Weekday/weekend times — only when activeMode == 'weekdayWeekend'
  - name: "The Warehouse - 1/Kitchen Energy Weekday On Time"
    unique_id: zipassist_631a3385_energy_weekday_on_time
    icon: mdi:clock-start

  - name: "The Warehouse - 1/Kitchen Energy Weekday Off Time"
    unique_id: zipassist_631a3385_energy_weekday_off_time
    icon: mdi:clock-end

  - name: "The Warehouse - 1/Kitchen Energy Weekend On Time"
    unique_id: zipassist_631a3385_energy_weekend_on_time
    icon: mdi:clock-start

  - name: "The Warehouse - 1/Kitchen Energy Weekend Off Time"
    unique_id: zipassist_631a3385_energy_weekend_off_time
    icon: mdi:clock-end

# --- services ---

## zipassist.clear_system_fault
# Clear a system fault on a hydrotap.
#
# Fields:
#   device_id (required): The hydrotap ID (UUID).
#   fault_id (required): The ID of the system fault to clear.
#
# Example:
#   service: zipassist.clear_system_fault
#   data:
#     device_id: "631a3385-301b-4c9c-97ed-3a1a50061f5c"
#     fault_id: "fault-abc123"

## zipassist.set_temperature
# Set the boiling or chilled water temperature.
#
# Fields:
#   device_id (required): The hydrotap ID (UUID).
#   water_type (required): "boiling" or "chilled".
#   temperature (required): Target temperature in °C.
#
# Example:
#   service: zipassist.set_temperature
#   data:
#     device_id: "631a3385-301b-4c9c-97ed-3a1a50061f5c"
#     water_type: "boiling"
#     temperature: 98.0

# --- sensor extra_state_attributes ---

## Filter sensors (filter_litres_remaining, filter_days_remaining, filter_estimated_days):
#   internal_filter_limit_litres: 6000
#   internal_filter_limit_days: 360
#   external_filter_limit_litres: null
#   external_filter_limit_days: null
#   building_name: "The Warehouse"
#   level: "1"
#   location_in_building: "Kitchen"
#   zip_managed: false
#   can_view: true
#   can_edit: true

## System fault details sensor:
#   faults:
#     - faultCode: "F01"
#       description: "Water leak detected"
#       timestamp: "2026-07-17T08:35:32+0000"

## Status log sensors (wifi_signal_strength, energy_*, sleep_mode_status, litres_filtered_*, days_filtered_*):
#   log_timestamp: "2026-07-17T08:35:32+0000"
#   time_since_last_log: "00:10:00"
#   hydrotap_active: true
