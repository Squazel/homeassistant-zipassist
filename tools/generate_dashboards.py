#!/usr/bin/env python3
"""
Generate Lovelace dashboard YAML for the ZipAssist CMMS integration.

Queries a running Home Assistant instance via its REST API to discover all
zipassist entities, groups them by HydroTap device, and emits a ready-to-use
dashboard YAML file with real entity IDs — no manual placeholder replacement.

Usage:
    python generate_dashboards.py                     \
        --ha-url http://homeassistant.local:8123       \
        --ha-token "eyJ..."                            \
        --output hydrotap-detail.yaml

    # Or use a .env file:
    python generate_dashboards.py --output hydrotap-detail.yaml

Environment variables:
    HA_URL     – Home Assistant base URL (default: http://localhost:8123)
    HA_TOKEN   – Long-lived access token (required)

Requires: pyyaml, requests
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

# Load .env if present
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
if ENV_PATH.exists():
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                val = val.strip().strip('"').strip("'")
                if key in ("HA_URL", "HA_TOKEN") and val and not os.environ.get(key):
                    os.environ[key] = val

# ---------------------------------------------------------------------------
# Entity key → dashboard card definition
# ---------------------------------------------------------------------------
# Each key maps to (domain, card_type, display_name, section)
# Sections mirror the website layout order.

ENTITY_LAYOUT: list[dict[str, Any]] = [
    # --- Section: Info & Status ---
    {"section": "Info & Status", "section_icon": "mdi:information-outline",
     "entities": [
         ("sensor", "status", "Status", "details"),
         ("sensor", "last_sync", "Last Sync", "details"),
         ("sensor", "serial_number", "Serial Number", "details"),
         ("sensor", "firmware_version", "Firmware", "details"),
         ("sensor", "wifi_signal_strength", "WiFi Signal", "details"),
         ("binary_sensor", "system_fault", "System Fault", "details"),
         ("sensor", "sleep_mode_status", "Sleep Mode", "details"),
    ]},
    # --- Section: Filter Life ---
    {"section": "Filter Life", "section_icon": "mdi:air-filter",
     "entities": [
         ("sensor", "filter_litres_remaining", "Filter Life (Litres)", "tile"),
         ("sensor", "filter_days_remaining", "Filter Life (Days)", "tile"),
         ("sensor", "filter_estimated_days", "Filter Est. Days", "tile"),
         ("sensor", "litres_filtered_internal", "Litres Filtered (Int)", "details"),
         ("sensor", "days_filtered_internal", "Days Filtered (Int)", "details"),
         ("sensor", "litres_filtered_external", "Litres Filtered (Ext)", "details"),
         ("sensor", "days_filtered_external", "Days Filtered (Ext)", "details"),
    ]},
    # --- Section: Usage ---
    {"section": "Usage", "section_icon": "mdi:water-percent",
     "entities": [
         ("sensor", "average_daily_usage", "Avg Daily Usage", "tile"),
         ("sensor", "peak_hourly_usage", "Peak Hourly Usage", "tile"),
         ("sensor", "energy_total", "Energy Total", "tile"),
         ("sensor", "energy_since_last_log", "Energy Since Last Log", "details"),
    ]},
    # --- Section: Safety & Security ---
    {"section": "Safety & Security", "section_icon": "mdi:shield-lock",
     "entities": [
         ("switch", "safety_lock", "Safety Lock", "controls"),
         ("switch", "hot_isolation", "Hot Isolation", "controls"),
         ("select", "sync_period", "Sync Period", "controls"),
    ]},
    # --- Section: Temperature ---
    {"section": "Temperature Settings", "section_icon": "mdi:thermometer",
     "entities": [
         ("number", "boiling_temp", "Boiling Temp", "controls"),
         ("number", "chilled_temp", "Chilled Temp", "controls"),
    ]},
    # --- Section: Dispense ---
    {"section": "Dispense Settings", "section_icon": "mdi:timer-outline",
     "entities": [
         ("number", "boiling_duration", "Boiling Duration", "controls"),
         ("number", "chilled_duration", "Chilled Duration", "controls"),
         ("number", "sparkling_duration", "Sparkling Duration", "controls"),
         ("number", "ambient_duration", "Ambient Duration", "controls"),
    ]},
    # --- Section: Filters (controls) ---
    {"section": "Filter Limits", "section_icon": "mdi:water-filter",
     "entities": [
         ("number", "internal_filter_litres", "Int Filter Life (L)", "controls"),
         ("number", "internal_filter_days", "Int Filter Life (Days)", "controls"),
         ("number", "external_filter_litres", "Ext Filter Life (L)", "controls"),
         ("number", "external_filter_days", "Ext Filter Life (Days)", "controls"),
    ]},
    # --- Section: On/Off Timers ---
    {"section": "On/Off Timers", "section_icon": "mdi:power-plug",
     "entities": [
         ("select", "energy_mode", "Active Mode", "controls"),
         # Everyday
         ("switch", "energy_everyday_on_active", "Everyday — On Active", "controls"),
         ("time", "energy_everyday_on_time", "Everyday — On Time", "controls"),
         ("switch", "energy_everyday_off_active", "Everyday — Off Active", "controls"),
         ("time", "energy_everyday_off_time", "Everyday — Off Time", "controls"),
         # Weekdays
         ("switch", "energy_weekday_on_active", "Weekdays — On Active", "controls"),
         ("time", "energy_weekday_on_time", "Weekdays — On Time", "controls"),
         ("switch", "energy_weekday_off_active", "Weekdays — Off Active", "controls"),
         ("time", "energy_weekday_off_time", "Weekdays — Off Time", "controls"),
         # Weekend
         ("switch", "energy_weekend_on_active", "Weekend — On Active", "controls"),
         ("time", "energy_weekend_on_time", "Weekend — On Time", "controls"),
         ("switch", "energy_weekend_off_active", "Weekend — Off Active", "controls"),
         ("time", "energy_weekend_off_time", "Weekend — Off Time", "controls"),
         # Daily (Mon–Sun)
         *[("switch", f"energy_daily_{d}_on_active", f"{d.title()} — On Active", "controls") for d in ("mon","tue","wed","thu","fri","sat","sun")],
         *[("time", f"energy_daily_{d}_on_time", f"{d.title()} — On Time", "controls") for d in ("mon","tue","wed","thu","fri","sat","sun")],
         *[("switch", f"energy_daily_{d}_off_active", f"{d.title()} — Off Active", "controls") for d in ("mon","tue","wed","thu","fri","sat","sun")],
         *[("time", f"energy_daily_{d}_off_time", f"{d.title()} — Off Time", "controls") for d in ("mon","tue","wed","thu","fri","sat","sun")],
    ]},
    # --- Section: Sleep Mode ---
    {"section": "Sleep Mode", "section_icon": "mdi:sleep",
     "entities": [
         ("select", "sleep_mode", "Sleep Mode", "controls"),
    ]},
]


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

class DashboardGenerator:
    """Generate Lovelace dashboards from a live Home Assistant instance."""

    def __init__(self, ha_url: str, token: str) -> None:
        self.ha_url = ha_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })

    def _get(self, path: str) -> dict | list | Any:
        """GET request to HA API."""
        resp = self.session.get(f"{self.ha_url}{path}", timeout=30)
        resp.raise_for_status()
        return resp.json()

    def discover_devices(self) -> dict[str, dict[str, str]]:
        """Discover zipassist devices and their entities from HA.

        Returns: {device_name: {key: entity_id}}
          device_name: human-readable display name, e.g. "The Warehouse - 1/Kitchen"
          key: entity key, e.g. "filter_litres_remaining"
          entity_id: full entity_id, e.g. "sensor.the_warehouse_1_kitchen_filter_litres_remaining"
        """
        states: list[dict] = self._get("/api/states")

        # Build a map of device_name → {key → entity_id}
        devices: dict[str, dict[str, str]] = {}
        seen_device_ids: dict[str, str] = {}  # unique_id_prefix → device_name

        for entity in states:
            eid = entity.get("entity_id", "")
            attrs = entity.get("attributes", {})

            # Only zipassist entities
            unique_id = attrs.get("unique_id")
            if not unique_id or not unique_id.startswith("zipassist_"):
                continue

            # Parse unique_id: zipassist_{hydrotap_uuid}_{entity_key}
            # e.g. zipassist_631a3385-301b-4c9c-97ed-3a1a50061f5c_filter_litres_remaining
            parts = unique_id.split("_", 1)  # ["zipassist", "uuid_key_key..."]
            if len(parts) < 2:
                continue
            rest = parts[1]

            # The key is everything after the last underscore? No — keys can have underscores.
            # The uuid is fixed-length (36 chars from 8-4-4-4-12). We need to find the boundary.
            # Simpler: check known keys. The uuid part + "_" + key.
            # UUID pattern: 8-4-4-4-12 hex chars = 36 chars
            # unique_id = "zipassist_" + uuid + "_" + key
            # So after "zipassist_", skip 36 chars + 1 underscore

            if len(rest) < 38:  # 36 uuid + at least "_x"
                continue
            uuid_str = rest[:36]
            entity_key = rest[37:]  # after uuid + underscore

            # Get device name from attributes
            dev_name = (attrs.get("device", {}) or {}).get("name") or "Unknown Device"
            if uuid_str not in seen_device_ids:
                seen_device_ids[uuid_str] = dev_name
            device_name = seen_device_ids[uuid_str]

            if device_name not in devices:
                devices[device_name] = {}
            devices[device_name][entity_key] = eid

        return devices

    def generate_dashboard(self, device_name: str, entities: dict[str, str]) -> dict:
        """Generate a complete dashboard YAML for one device."""
        sections: list[dict] = []

        for section_def in ENTITY_LAYOUT:
            section_title = section_def["section"]
            section_icon = section_def.get("section_icon", "")

            # Collect available entities for this section
            section_entities: list[dict] = []
            for domain, key, display_name, card_type in section_def["entities"]:
                if key in entities:
                    section_entities.append({
                        "entity": entities[key],
                        "name": display_name,
                    })

            if not section_entities:
                continue

            # Group entities by card_type for this section
            tiles = [e for e in section_entities if card_type == "tile" for _, card_type in [(e, "check")] if any(t[3] == "tile" for t in section_def["entities"] if t[1] == "key_placeholder")]
            # Simpler approach: just add the entities list card for each section

            # Build the section
            if section_icon:
                sections.append({
                    "type": "heading",
                    "heading": section_title,
                    "icon": section_icon,
                })
            else:
                sections.append({
                    "type": "heading",
                    "heading": section_title,
                })

            # Add entities card
            card: dict[str, Any] = {
                "type": "entities",
                "show_header_toggle": False,
                "entities": [
                    {"entity": e["entity"], "name": e["name"]}
                    for e in section_entities
                ],
            }
            sections.append(card)

        dashboard = {
            "title": f"HydroTap — {device_name}",
            "views": [{
                "title": "HydroTap",
                "path": "hydrotap",
                "icon": "mdi:water-pump",
                "type": "sections",
                "max_columns": 3,
                "sections": sections,
            }],
        }
        return dashboard


    def generate_all(self, output_dir: str | Path) -> list[Path]:
        """Generate dashboard files for all discovered devices."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        devices = self.discover_devices()
        if not devices:
            print("No zipassist devices found. Is the integration configured?")
            return []

        files: list[Path] = []
        for device_name, entities in sorted(devices.items()):
            # Slugify device name for filename
            slug = device_name.lower()
            for ch in " /\\()[]{}-":
                slug = slug.replace(ch, "_")
            slug = "_".join(slug.split("_")[:4])  # Keep first 4 parts

            dashboard = self.generate_dashboard(device_name, entities)

            filepath = output_dir / f"zipassist-{slug}.yaml"
            with open(filepath, "w") as f:
                f.write("# Generated by ZipAssist dashboard generator\n")
                f.write(f"# Device: {device_name}\n")
                f.write(f"# {len(entities)} entities\n\n")
                yaml.dump(dashboard, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

            files.append(filepath)
            print(f"  ✓ {filepath} ({len(entities)} entities)")

        return files


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate ZipAssist Lovelace dashboards from a live HA instance.",
    )
    parser.add_argument(
        "--ha-url",
        default=os.environ.get("HA_URL", "http://localhost:8123"),
        help="Home Assistant base URL (env: HA_URL, default: http://localhost:8123)",
    )
    parser.add_argument(
        "--ha-token",
        default=os.environ.get("HA_TOKEN", ""),
        help="Long-lived access token (env: HA_TOKEN)",
    )
    parser.add_argument(
        "-o", "--output-dir",
        default=Path(__file__).resolve().parent,
        help="Output directory for generated dashboard files",
    )
    return parser.parse_args()


def main() -> None:
    try:
        import requests as _requests
        import yaml as _yaml
    except ImportError:
        print("This script requires 'requests' and 'pyyaml'.")
        print("Run: pip install requests pyyaml")
        sys.exit(1)

    args = parse_args()

    if not args.ha_token:
        print("ERROR: --ha-token is required (or set HA_TOKEN environment variable)")
        print("")
        print("Create a long-lived access token in Home Assistant:")
        print("  Profile → Security → Long-Lived Access Tokens → Create Token")
        sys.exit(1)

    print(f"Connecting to {args.ha_url} ...")
    gen = DashboardGenerator(args.ha_url, args.ha_token)

    print("Discovering zipassist entities ...")
    files = gen.generate_all(args.output_dir)

    if files:
        print(f"\nGenerated {len(files)} dashboard file(s) in {args.output_dir}")
        print("\nTo use, add this to your Home Assistant configuration.yaml:")
        print()
        print("  lovelace:")
        print("    mode: storage")
        print("    dashboards:")
        for fpath in files:
            print(f"      {fpath.stem}:")
            print(f"        mode: yaml")
            print(f"        title: {fpath.stem.replace('-', ' ').title()}")
            print(f"        filename: {fpath.name}")
        print()
    else:
        print("No devices found.")


if __name__ == "__main__":
    main()
