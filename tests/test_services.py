"""Tests for the ZipAssist services."""

from __future__ import annotations

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "custom_components"),
)

from zipassist.services import async_setup_services, async_unload_services  # noqa: E402


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

        hass.services.async_register.assert_called_once()
        call_args = hass.services.async_register.call_args
        assert call_args.args[0] == "zipassist"
        assert call_args.args[1] == "clear_system_fault"

        # Unload
        async_unload_services(hass)
        hass.services.async_remove.assert_called_once_with(
            "zipassist", "clear_system_fault"
        )

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

        # Get the registered handler
        register_call = hass.services.async_register.call_args
        handler = register_call.kwargs.get(
            "schema", register_call.args[2] if len(register_call.args) > 2 else None
        )
        # Actually the handler is the second positional arg
        handler = register_call.args[2]

        # Call the handler
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

        register_call = hass.services.async_register.call_args
        handler = register_call.args[2]

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
        # Put a non-coordinator in hass.data
        hass.data = {
            "zipassist": {
                "test_entry": MagicMock(client=None),  # no client attr
            }
        }
        hass.services = MagicMock()
        hass.services.async_register = MagicMock()

        await async_setup_services(hass)

        register_call = hass.services.async_register.call_args
        handler = register_call.args[2]

        await handler(
            MagicMock(
                data={"device_id": "any", "fault_id": "fault-1"}
            )
        )

        mock_coordinator.client.clear_fault.assert_not_called()