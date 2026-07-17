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
# TODO: implement after coordinator polling is stable

number:
  - name: "The Warehouse - 1/Kitchen Boiling Temperature"
    unique_id: zipassist_631a3385_boiling_temp
    native_min_value: 68
    native_max_value: 100
    native_step: 1
    native_unit_of_measurement: "°C"

  - name: "The Warehouse - 1/Kitchen Chilled Temperature"
    unique_id: zipassist_631a3385_chilled_temp
    native_min_value: 2
    native_max_value: 15
    native_step: 1
    native_unit_of_measurement: "°C"

# --- binary sensors (future) ---

binary_sensor:
  - name: "The Warehouse - 1/Kitchen Safety Lock"
    unique_id: zipassist_631a3385_safety_lock
    icon: mdi:lock

  - name: "The Warehouse - 1/Kitchen Hot Isolation"
    unique_id: zipassist_631a3385_hot_isolation
    icon: mdi:water-off
