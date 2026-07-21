# Dashboards & Cards

The ZipAssist integration includes a **custom Lovelace card** that loads
automatically when the integration is installed — no configuration required.
It mirrors the layout of the official
[ZipAssist CMMS website](https://zipassist.zipindustries.com/).

> **How it works:** When Home Assistant starts, the integration registers
> the card with the frontend. It appears in the Lovelace card picker as
> "ZipAssist HydroTap". Add it to any dashboard, select your HydroTap
> device, and the card maps that device's entities automatically.

---

## Quick Start

1. Install and configure the ZipAssist CMMS integration
2. Restart Home Assistant (the card auto-registers on startup)
3. Edit any dashboard → **Add Card** → search for **"ZipAssist"**
4. Select **"ZipAssist HydroTap"**
5. Choose your HydroTap **device** in the card editor (required)
6. Optionally set a custom **title**

### Card shows “custom element doesn't exist”

That message means Lovelace rendered the dashboard **before** `zipassist-card.js`
finished loading (or the script never loaded). It is a **load/registration**
issue, not a bad card config.

1. Confirm the file is served: open  
   `http://HOME_ASSISTANT/zipassist/zipassist-card.js?v=VERSION`  
   (VERSION = integration version in `manifest.json`). You should see JavaScript.
2. Hard-refresh the dashboard (Ctrl+F5 / empty cache). The card dispatches
   `ll-rebuild` after it defines the element so a late load can recover.
3. If it still flaps, your HA may be unable to write **Lovelace resources**
   (e.g. `.storage/lovelace_resources` version newer than the core). Fix by
   upgrading HA or restoring a matching backup. Until then, add a resource
   manually:

   **Settings → Dashboards → ⋮ → Resources → Add resource**

   - URL: `/zipassist/zipassist-card.js?v=0.1.11` (match current version)
   - Type: **JavaScript module**

4. YAML mode: add the same URL under `lovelace.resources` with `type: module`.

### YAML example

```yaml
type: custom:zipassist-card
device: DEVICE_REGISTRY_ID   # or a device name substring, e.g. "Kitchen"
title: "Office Tap"         # optional
```

In the visual editor, pick the device from the ZipAssist device selector.
For YAML, `device` may be the device registry id **or** a case-insensitive
substring of the device name.

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

Each section is collapsible — click a section heading to hide/show its rows. Tiles and labels open the entity more-info dialog. Switches, numbers, selects, and times are editable inline.

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
