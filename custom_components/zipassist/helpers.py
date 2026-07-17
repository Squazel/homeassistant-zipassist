"""Shared helpers for the ZipAssist CMMS integration."""

from __future__ import annotations

from typing import Any


def device_name(hydrotap: dict[str, Any]) -> str:
    """Build the HA device name from location fields.

    Format: "{buildingName} - {level}/{locationInBuilding}"
    Falls back to buildingName alone, then moduleName.
    """
    loc: dict[str, Any] = hydrotap.get("hydrotapLocation") or {}
    building: str = str(loc.get("buildingName", "")).strip()
    level: str = str(loc.get("level", "")).strip()
    location: str = str(loc.get("locationInBuilding", "")).strip()
    if building and (level or location):
        detail = "/".join(p for p in (level, location) if p)
        return f"{building} - {detail}"
    if building:
        return building
    return str(hydrotap.get("moduleName", "Unknown"))