"""Services for the ZipAssist CMMS integration."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_CLEAR_FAULT = "clear_system_fault"
SERVICE_SET_TEMPERATURE = "set_temperature"

CLEAR_FAULT_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): str,
        vol.Required("fault_id"): str,
    }
)

SET_TEMPERATURE_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): str,
        vol.Required("water_type"): vol.In(["boiling", "chilled"]),
        vol.Required("temperature"): vol.Coerce(float),
    }
)


def _find_coordinator_for_device(
    hass: HomeAssistant, device_id: str
) -> tuple[Any | None, str | None]:
    """Find the coordinator and hydrotap_id that owns the given device_id.

    Returns (coordinator, hydrotap_id) or (None, None) if not found.
    """
    for coord in hass.data.get(DOMAIN, {}).values():
        if not hasattr(coord, "client"):
            continue
        for h in coord.data.get("hydrotaps", []):
            if h.get("hydrotapId") == device_id:
                return coord, device_id
    return None, None


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register ZipAssist services (idempotent)."""
    # Prefer an explicit domain data flag so unit tests / MagicMocks that
    # make has_service truthy by default do not skip registration incorrectly.
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("services_registered"):
        return

    async def _handle_clear_fault(call: ServiceCall) -> None:
        """Handle the clear_system_fault service call."""
        device_id: str = call.data["device_id"]
        fault_id: str = call.data["fault_id"]

        coordinator, hydrotap_id = _find_coordinator_for_device(hass, device_id)
        if coordinator is None:
            _LOGGER.error("Device %s not found in any ZipAssist entry", device_id)
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

    async def _handle_set_temperature(call: ServiceCall) -> None:
        """Handle the set_temperature service call."""
        device_id: str = call.data["device_id"]
        water_type: str = call.data["water_type"]
        temperature: float = call.data["temperature"]

        coordinator, hydrotap_id = _find_coordinator_for_device(hass, device_id)
        if coordinator is None:
            _LOGGER.error("Device %s not found in any ZipAssist entry", device_id)
            return

        payload = {water_type: {"temp": temperature}}
        success = await coordinator.client.update_settings(hydrotap_id, payload)
        if success:
            _LOGGER.info(
                "Set %s temperature to %.1f°C on %s",
                water_type,
                temperature,
                hydrotap_id,
            )
            await coordinator.async_request_refresh()
        else:
            _LOGGER.error(
                "Failed to set %s temperature on %s", water_type, hydrotap_id
            )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_FAULT,
        _handle_clear_fault,
        schema=CLEAR_FAULT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TEMPERATURE,
        _handle_set_temperature,
        schema=SET_TEMPERATURE_SCHEMA,
    )
    domain_data["services_registered"] = True


def async_unload_services(hass: HomeAssistant) -> None:
    """Unregister ZipAssist services."""
    for service in (SERVICE_CLEAR_FAULT, SERVICE_SET_TEMPERATURE):
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)
    if DOMAIN in hass.data:
        hass.data[DOMAIN].pop("services_registered", None)