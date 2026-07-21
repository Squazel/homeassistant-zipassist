"""Tests for the ZipAssist services."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "custom_components"),
)

from zipassist.services import (  # noqa: E402
    SERVICE_CLEAR_FAULT,
    SERVICE_SET_TEMPERATURE,
    async_setup_services,
    async_unload_services,
)


def _get_handler(hass_mock, service_name: str):
    """Extract the handler registered for a given service name."""
    for call in hass_mock.services.async_register.call_args_list:
        args = call.args
        if args[0] == "zipassist" and args[1] == service_name:
            return args[2]
    return None


class TestServices:
    """Tests for service registration and handling."""

    @pytest.mark.asyncio
    async def test_setup_and_unload_services(self) -> None:
        """Test services are registered and unregistered."""
        hass = MagicMock()
        hass.services = MagicMock()
        hass.services.async_register = MagicMock()
        hass.services.has_service = MagicMock(return_value=True)
        hass.services.async_remove = MagicMock()

        await async_setup_services(hass)

        assert hass.services.async_register.call_count == 2
        # Check both services were registered
        registered = {
            call.args[1]
            for call in hass.services.async_register.call_args_list
        }
        assert registered == {SERVICE_CLEAR_FAULT, SERVICE_SET_TEMPERATURE}

        # Unload
        async_unload_services(hass)
        assert hass.services.async_remove.call_count == 2

    @pytest.mark.asyncio
    async def test_clear_fault_success(
        self, mock_coordinator, sample_hydrotap
    ) -> None:
        """Test clear_system_fault service with valid device."""
        hass = MagicMock()
        hass.data = {
            "zipassist": {
                "test_entry": mock_coordinator,
            }
        }
        hass.services = MagicMock()
        hass.services.async_register = MagicMock()

        await async_setup_services(hass)

        handler = _get_handler(hass, SERVICE_CLEAR_FAULT)
        assert handler is not None

        await handler(
            MagicMock(
                data={
                    "device_id": sample_hydrotap["hydrotapId"],
                    "fault_id": "fault-1",
                }
            )
        )

        mock_coordinator.client.clear_fault.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_fault_device_not_in_data(
        self, mock_coordinator
    ) -> None:
        """Test clear_fault with unknown device_id."""
        mock_coordinator.data["hydrotaps"] = []

        hass = MagicMock()
        hass.data = {
            "zipassist": {
                "test_entry": mock_coordinator,
            }
        }
        hass.services = MagicMock()
        hass.services.async_register = MagicMock()

        await async_setup_services(hass)

        handler = _get_handler(hass, SERVICE_CLEAR_FAULT)
        await handler(
            MagicMock(
                data={"device_id": "unknown-id", "fault_id": "fault-1"}
            )
        )

        mock_coordinator.client.clear_fault.assert_not_called()

    @pytest.mark.asyncio
    async def test_clear_fault_no_coordinator(self, mock_coordinator) -> None:
        """Test clear_fault with no coordinator in hass.data."""
        hass = MagicMock()
        hass.data = {
            "zipassist": {
                "test_entry": MagicMock(client=None),  # no client attr
            }
        }
        hass.services = MagicMock()
        hass.services.async_register = MagicMock()

        await async_setup_services(hass)

        handler = _get_handler(hass, SERVICE_CLEAR_FAULT)
        await handler(
            MagicMock(
                data={"device_id": "any", "fault_id": "fault-1"}
            )
        )

        mock_coordinator.client.clear_fault.assert_not_called()

    # ------------------------------------------------------- set_temperature

    @pytest.mark.asyncio
    async def test_set_temperature_success(
        self, mock_coordinator, sample_hydrotap
    ) -> None:
        """Test set_temperature service with valid device."""
        hass = MagicMock()
        hass.data = {
            "zipassist": {
                "test_entry": mock_coordinator,
            }
        }
        hass.services = MagicMock()
        hass.services.async_register = MagicMock()

        await async_setup_services(hass)

        handler = _get_handler(hass, SERVICE_SET_TEMPERATURE)
        assert handler is not None

        await handler(
            MagicMock(
                data={
                    "device_id": sample_hydrotap["hydrotapId"],
                    "water_type": "boiling",
                    "temperature": 98.0,
                }
            )
        )

        mock_coordinator.client.update_settings.assert_called_once_with(
            sample_hydrotap["hydrotapId"],
            {"boiling": {"temp": 98.0}},
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_temperature_chilled(
        self, mock_coordinator, sample_hydrotap
    ) -> None:
        """Test set_temperature for chilled water."""
        hass = MagicMock()
        hass.data = {
            "zipassist": {
                "test_entry": mock_coordinator,
            }
        }
        hass.services = MagicMock()
        hass.services.async_register = MagicMock()

        await async_setup_services(hass)

        handler = _get_handler(hass, SERVICE_SET_TEMPERATURE)
        await handler(
            MagicMock(
                data={
                    "device_id": sample_hydrotap["hydrotapId"],
                    "water_type": "chilled",
                    "temperature": 5.0,
                }
            )
        )

        mock_coordinator.client.update_settings.assert_called_once_with(
            sample_hydrotap["hydrotapId"],
            {"chilled": {"temp": 5.0}},
        )

    @pytest.mark.asyncio
    async def test_set_temperature_unknown_device(
        self, mock_coordinator
    ) -> None:
        """Test set_temperature with unknown device_id."""
        mock_coordinator.data["hydrotaps"] = []

        hass = MagicMock()
        hass.data = {
            "zipassist": {
                "test_entry": mock_coordinator,
            }
        }
        hass.services = MagicMock()
        hass.services.async_register = MagicMock()

        await async_setup_services(hass)

        handler = _get_handler(hass, SERVICE_SET_TEMPERATURE)
        await handler(
            MagicMock(
                data={
                    "device_id": "unknown-id",
                    "water_type": "boiling",
                    "temperature": 98.0,
                }
            )
        )

        mock_coordinator.client.update_settings.assert_not_called()