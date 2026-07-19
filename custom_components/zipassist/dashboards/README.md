# ZipAssist CMMS — Home Assistant Dashboards & Cards

The integration includes a **custom Lovelace card** (`zipassist-card`) that
loads automatically when the integration is installed.

## How to use

1. Install and configure the ZipAssist CMMS integration
2. Restart Home Assistant
3. Edit any dashboard → **Add Card** → search for **"ZipAssist"**
4. Select **"ZipAssist HydroTap"** — it auto-discovers your entities

For more details, see [docs/dashboards.md](../../docs/dashboards.md).

## Advanced: YAML Dashboard Generator

For users who prefer standalone dashboard YAML files (rather than cards),
a generator script is available at `tools/generate_dashboards.py`.
