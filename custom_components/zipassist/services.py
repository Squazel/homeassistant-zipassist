"""Services for the ZipAssist CMMS integration."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_CLEAR_FAULT = "clear_system_fault"

CLEAR_FAULT_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): str,
        vol.Required("fault_id"): str,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register ZipAssist services."""

    async def _handle_clear_fault(call: ServiceCall) -> None:
        """Handle the clear_system_fault service call."""
        device_id: str = call.data["device_id"]
        fault_id: str = call.data["fault_id"]

        # Find the coordinator for this device
        coordinator = None
        for entry_id, coord in hass.data.get(DOMAIN, {}).items():
            if not hasattr(coord, "client"):
                continue
            coordinator = coord
            break

        if coordinator is None:
            _LOGGER.error("No ZipAssist coordinator found")
            return

        # Find the hydrotap ID from the device ID
        hydrotap_id = None
        for h in coordinator.data.get("hydrotaps", []):
            if h.get("hydrotapId") == device_id:
                hydrotap_id = device_id
                break

        if not hydrotap_id:
            _LOGGER.error("Device %s not found", device_id)
            return

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000")
        success = await coordinator.client.clear_fault(
            hydrotap_id, fault_id, now
        )
        if success:
            _LOGGER.info("Cleared fault %s on %s", fault_id, hydrotap_id)
            await coordinator.async_request_refresh()
        else:
            _LOGGER.error(
                "Failed to clear fault %s on %s", fault_id, hydrotap_id
            )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_FAULT,
        _handle_clear_fault,
        schema=CLEAR_FAULT_SCHEMA,
    )


def async_unload_services(hass: HomeAssistant) -> None:
    """Unregister ZipAssist services."""
    if hass.services.has_service(DOMAIN, SERVICE_CLEAR_FAULT):
        hass.services.async_remove(DOMAIN, SERVICE_CLEAR_FAULT)