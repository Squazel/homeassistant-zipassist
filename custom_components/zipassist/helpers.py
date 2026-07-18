"""Shared helpers for the ZipAssist CMMS integration."""

from __future__ import annotations

from typing import Any


def device_name(hydrotap: dict[str, Any]) -> str:
    """Build the HA device name from location fields.

    Format: "{buildingName} - {level}/{locationInBuilding}"
    Falls back to buildingName alone, then moduleName.

    Supports both nested (hydrotapLocation dict, from detail endpoint)
    and flat (buildingName/level/locationInBuilding, from list endpoint).
    """
    loc: dict[str, Any] = hydrotap.get("hydrotapLocation") or {}
    building: str = str(
        loc.get("buildingName") or hydrotap.get("buildingName") or ""
    ).strip()
    level: str = str(
        loc.get("level") or hydrotap.get("level") or ""
    ).strip()
    location: str = str(
        loc.get("locationInBuilding") or hydrotap.get("locationInBuilding") or ""
    ).strip()
    if building and (level or location):
        detail = "/".join(p for p in (level, location) if p)
        return f"{building} - {detail}"
    if building:
        return building
    return str(hydrotap.get("moduleName", "Unknown"))