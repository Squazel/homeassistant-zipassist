"""Shared helpers for the ZipAssist CMMS integration."""

from __future__ import annotations


def device_name(hydrotap: dict) -> str:
    """Build the HA device name from location fields.

    Format: "{buildingName} - {level}/{locationInBuilding}"
    Falls back to buildingName alone, then moduleName.
    """
    loc = hydrotap.get("hydrotapLocation") or {}
    building = loc.get("buildingName", "").strip()
    level = loc.get("level", "").strip()
    location = loc.get("locationInBuilding", "").strip()
    if building and (level or location):
        detail = "/".join(p for p in (level, location) if p)
        return f"{building} - {detail}"
    if building:
        return building
    return hydrotap.get("moduleName", "Unknown")