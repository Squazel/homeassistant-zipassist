# Dashboards & Cards

The ZipAssist integration includes a **custom Lovelace card** that loads
automatically when the integration is installed — no configuration required.
It mirrors the layout of the official
[ZipAssist CMMS website](https://zipassist.zipindustries.com/).

> **How it works:** When Home Assistant starts, the integration registers
> the card with the frontend. It appears in the Lovelace card picker as
> "ZipAssist HydroTap". Add it to any dashboard and it auto-discovers your
> HydroTap entities.

---

## Quick Start

1. Install and configure the ZipAssist CMMS integration
2. Restart Home Assistant (the card auto-registers on startup)
3. Edit any dashboard → **Add Card** → search for **"ZipAssist"**
4. Select **"ZipAssist HydroTap"**
5. The card auto-discovers your HydroTap entities — no additional config needed

### Optional: Filter by device

If you have multiple HydroTaps, you can add a `device` option to show
only one (partial name match works):

```yaml
type: custom:zipassist-card
device: "Kitchen"
```

### Optional: Custom title

```yaml
type: custom:zipassist-card
title: "Office Tap"
```

---

## Card Layout

The card mirrors the website's individual HydroTap management page with
collapsible sections:

| # | Section | Card Type | Description |
|---|---------|-----------|-------------|
| 1 | **Info & Status** | Tiles | Device status, serial, firmware, WiFi signal, sleep mode, system fault |
| 2 | **Filter Life** | Tiles | Remaining litres, days, estimated days |
| 3 | **Usage** | Tiles | Average daily usage, peak hourly usage, energy total |
| 4 | **Safety & Security** | Rows + switches | Safety lock, hot isolation, sync period |
| 5 | **Temperature** | Rows | Boiling/chilled temperature controls |
| 6 | **Dispense Settings** | Rows | Dispense duration controls |
| 7 | **Filter Limits** | Rows | Internal/external filter litre and day limits |
| 8 | **On/Off Timers** | Rows | Energy mode select, everyday/daily/weekday-weekend switches & times |
| 9 | **Sleep Mode** | Rows | Sleep mode selection |

Sections and individual entities are **skipped automatically** if your
HydroTap model doesn't support them (e.g., no chilled feature → no
chilled temp control visible).

The card is collapsible — click the header bar to hide/show all sections.

---

## Using entities directly

The card is optional. All 70 entities are standard Home Assistant entities
— use them directly in automations, scripts, or any other Lovelace card.

```yaml
# Example: Manual entities card for just temperature controls
type: entities
entities:
  - number.kitchen_hydrotap_boiling_temp
  - number.kitchen_hydrotap_chilled_temp
```

The full entity reference is in [Entities](entities.md).

## Building custom dashboards

All entities follow the naming pattern:

```
{domain}.{device_name_slug}_{entity_key}
```

Device names become slugs by lowercasing and replacing separators with
underscores.  For example, device "My Office — 1/Kitchen" becomes
`my_office_1_kitchen`.

You can find the actual entity IDs of your devices in
**Settings → Devices & Services → Entities**, filtering by
`zipassist`.

The full entity reference is available in [Entities](entities.md).
