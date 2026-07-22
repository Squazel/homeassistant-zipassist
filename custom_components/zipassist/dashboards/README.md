# ZipAssist CMMS — Home Assistant Dashboards & Cards

The integration includes a **custom Lovelace card** (`zipassist-card`) that
loads automatically when the integration is installed.

## How to use

1. Install and configure the ZipAssist CMMS integration
2. Restart Home Assistant
3. Edit any dashboard → **Add Card** → search for **"ZipAssist"**
4. Select **"ZipAssist HydroTap"**
5. Choose your HydroTap device (required) and optional title

The card discovers entities for the selected device and exposes controls for
switches, numbers, selects, and times. Status sections use tiles with more-info.

For more details, see [docs/dashboards.md](../../docs/dashboards.md).
