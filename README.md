# ZipAssist CMMS - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant integration for the [ZipAssist CMMS](https://zipassist.zipindustries.com/) platform by Zip Industries. Monitor and manage your Zip HydroTaps through Home Assistant.

## Features

- Monitor HydroTap status and usage
- View logs and maintenance data
- Read and write device settings
- Filter change reminders
- Error and notification tracking

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