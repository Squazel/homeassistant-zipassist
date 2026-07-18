"""Tests for the helpers module."""

from __future__ import annotations

import os
import sys

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "custom_components", "zipassist"
    ),
)

from helpers import device_name  # noqa: E402


class TestDeviceName:
    """Tests for device_name helper."""

    def test_full_location(self) -> None:
        """Test device name with building, level, and location."""
        hydrotap = {
            "hydrotapLocation": {
                "buildingName": "The Warehouse",
                "level": "1",
                "locationInBuilding": "Kitchen",
            },
            "moduleName": "BC 100/75",
        }
        assert device_name(hydrotap) == "The Warehouse - 1/Kitchen"

    def test_building_and_level_only(self) -> None:
        """Test device name with building and level, no location."""
        hydrotap = {
            "hydrotapLocation": {
                "buildingName": "Office",
                "level": "2",
                "locationInBuilding": "",
            },
            "moduleName": "AI 200",
        }
        assert device_name(hydrotap) == "Office - 2"

    def test_building_and_location_only(self) -> None:
        """Test device name with building and location, no level."""
        hydrotap = {
            "hydrotapLocation": {
                "buildingName": "Office",
                "level": "",
                "locationInBuilding": "Lobby",
            },
            "moduleName": "AI 200",
        }
        assert device_name(hydrotap) == "Office - Lobby"

    def test_building_only(self) -> None:
        """Test device name with only building."""
        hydrotap = {
            "hydrotapLocation": {
                "buildingName": "Office",
                "level": "",
                "locationInBuilding": "",
            },
            "moduleName": "AI 200",
        }
        assert device_name(hydrotap) == "Office"

    def test_no_location_dict(self) -> None:
        """Test device name falls back to moduleName when no location."""
        hydrotap = {"moduleName": "BC 100/75"}
        assert device_name(hydrotap) == "BC 100/75"

    def test_empty_location_dict(self) -> None:
        """Test device name with empty location dict."""
        hydrotap = {"hydrotapLocation": {}, "moduleName": "BC 100/75"}
        assert device_name(hydrotap) == "BC 100/75"

    def test_no_module_name(self) -> None:
        """Test device name with no location and no moduleName."""
        hydrotap = {}
        assert device_name(hydrotap) == "Unknown"

    def test_whitespace_handling(self) -> None:
        """Test whitespace is stripped from location fields."""
        hydrotap = {
            "hydrotapLocation": {
                "buildingName": "  Office  ",
                "level": " 3 ",
                "locationInBuilding": " Lobby ",
            },
            "moduleName": "AI 200",
        }
        assert device_name(hydrotap) == "Office - 3/Lobby"

    def test_list_endpoint_fields(self) -> None:
        """Test with flat fields from list endpoint (no hydrotapLocation)."""
        hydrotap = {
            "buildingName": "The Warehouse",
            "level": "1",
            "locationInBuilding": "Kitchen",
            "moduleName": "BC 100/75",
        }
        assert device_name(hydrotap) == "The Warehouse - 1/Kitchen"