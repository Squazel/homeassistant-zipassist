"""The ZipAssist CMMS integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .client import ZipAssistClient
from .const import DEFAULT_BASE_URL, DOMAIN
from .coordinator import ZipAssistCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the ZipAssist CMMS component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ZipAssist CMMS from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    client = ZipAssistClient(
        email=entry.data["email"],
        password=entry.data["password"],
        base_url=entry.data.get("base_url", DEFAULT_BASE_URL),
    )

    if not await client.authenticate():
        _LOGGER.error("Failed to authenticate with ZipAssist")
        return False

    coordinator = ZipAssistCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id, None)
        if coordinator:
            await coordinator.client.close()
    return unload_ok