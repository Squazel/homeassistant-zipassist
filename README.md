# ZipAssist CMMS - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant integration for the [ZipAssist CMMS](https://zipassist.zipindustries.com/) platform by Zip Industries. Monitor and manage your Zip HydroTaps through Home Assistant.

## Features

- **74 entities** across 6 platforms: sensors, binary sensors, switches, numbers, selects, and times
- **Custom Lovelace card** — auto-loaded, mirrors the official ZipAssist website layout with collapsible red-bar sections, Zip-style YES/NO toggles, and nested On/Off timer tabs
- **Dashboard generator** — Python script (`tools/generate_dashboards.py`) auto-discovers entities and emits ready-to-use dashboard YAML
- **Read/write settings** — change temperatures, dispense durations, filter limits, safety toggles, energy schedules, sleep mode, and sync period
- **Filter monitoring** — remaining litres, days, estimated days, plus internal/external filter usage and limits
- **System fault tracking** — active fault detection with details and a `clear_system_fault` service
- **Energy timer management** — Everyday, Weekday/Weekend, and Daily (Mon–Sun) on/off schedules with switches and time controls
- **Sleep mode** — select sleep mode with human-readable status resolved from the API
- **Services** — `clear_system_fault` and `set_temperature` for automation use
- **Config flow** — UI-based setup with email/password, reauth support

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Search for "ZipAssist CMMS" in HACS
3. Install the integration
4. Restart Home Assistant

### Manual

Copy the `custom_components/zipassist` folder to your Home Assistant `custom_components` directory.

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "ZipAssist CMMS"
3. Enter your ZipAssist credentials (email and password)

Each HydroTap appears as a separate device named `{buildingName} - {level}/{location}`.

## Lovelace Card

After setup and a restart, the ZipAssist HydroTap card is available in the card picker. Add it to any dashboard, select your HydroTap device, and the card maps all entities automatically.

The card mirrors the official ZipAssist website with:
- **Device info** header block (status, serial, firmware, WiFi, filter life, usage)
- **Collapsible red-bar sections**: Safety Settings, Sync Time, System Fault Alerts, Filters, Dispense Settings, Temperature Settings, On/Off Timers, Sleep Mode
- **Nested timer tabs**: Everyday / Weekday-Weekend / Daily with per-day controls
- **Zip-style YES/NO toggles** for safety and energy switches

See [Dashboards](docs/dashboards.md) for full details.

## Entity Summary

| Platform | Count | Examples |
|---|---|---|
| Sensor | 18 | Filter life, usage, status, firmware, WiFi, energy, sleep mode status |
| Binary Sensor | 1 | System fault (PROBLEM device class) |
| Switch | 22 | Safety lock, hot isolation, 20 energy timer actives |
| Number | 10 | Boiling/chilled temp, 4 dispense durations, 4 filter limits |
| Select | 3 | Sleep mode, energy mode, sync period |
| Time | 20 | Energy on/off schedule times (everyday, weekday/weekend, daily) |

See [Entities](docs/entities.md) for the complete reference.

## Services

| Service | Description |
|---|---|
| `zipassist.clear_system_fault` | Clear a fault by `device_id` + `fault_id` |
| `zipassist.set_temperature` | Set boiling/chilled temp by `device_id` + `water_type` + `temperature` |

## Documentation

- [API Endpoints](docs/api-endpoints.md) — Full reference of all known ZipAssist CMMS API endpoints
- [Entities](docs/entities.md) — All 74 Home Assistant entities across 6 platforms
- [Dashboards](docs/dashboards.md) — Auto-loaded Lovelace card and layout reference
- [Architecture](docs/architecture.md) — Integration architecture and design decisions
- [Development](docs/development.md) — Local development setup, testing, and API exploration
- [TODO](TODO.md) — Remaining work items

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .
```

## License

MIT