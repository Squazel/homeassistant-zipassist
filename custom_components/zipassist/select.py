"""Select platform for ZipAssist CMMS — sleep mode and energy mode."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .helpers import device_name

_LOGGER = logging.getLogger(__name__)

# Sleep mode codes from the API
SLEEP_MODE_OPTIONS: list[str] = [
    "0", "1", "2", "3", "4", "5", "6", "7", "8",
]

ENERGY_MODE_OPTIONS: list[str] = [
    "everyday",
    "daily",
    "weekdayWeekend",
]


@dataclass(frozen=True, kw_only=True)
class ZipAssistSelectEntityDescription(SelectEntityDescription):
    """Description for a ZipAssist select entity."""

    value_fn: Callable[[dict], str | None]
    options_fn: Callable[[], list[str]]
    payload_fn: Callable[[str], dict]
    available_fn: Callable[[dict], bool] = lambda s: True


def _sleep_payload(value: str) -> dict:
    return {"sleepModeCode": int(value)}


def _energy_payload(value: str) -> dict:
    return {"energy": {"activeMode": value}}


SELECT_TYPES: tuple[ZipAssistSelectEntityDescription, ...] = (
    ZipAssistSelectEntityDescription(
        key="sleep_mode",
        translation_key="sleep_mode",
        icon="mdi:sleep",
        value_fn=lambda s: str(s.get("sleepModeCode", "")),
        options_fn=lambda: SLEEP_MODE_OPTIONS,
        payload_fn=_sleep_payload,
    ),
    ZipAssistSelectEntityDescription(
        key="energy_mode",
        translation_key="energy_mode",
        icon="mdi:power-plug",
        value_fn=lambda s: (s.get("energy") or {}).get("activeMode", ""),
        options_fn=lambda: ENERGY_MODE_OPTIONS,
        payload_fn=_energy_payload,
    ),
)


class ZipAssistSelect(CoordinatorEntity, SelectEntity):
    """Select entity for a ZipAssist hydrotap setting."""

    entity_description: ZipAssistSelectEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        hydrotap: dict,
        description: ZipAssistSelectEntityDescription,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._hydrotap_id: str = hydrotap["hydrotapId"]
        self.entity_description = description
        self._attr_unique_id = f"{self._hydrotap_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._hydrotap_id)},
            name=device_name(hydrotap),
            manufacturer="Zip Industries",
            model=hydrotap.get("moduleName"),
            sw_version=hydrotap.get("firmwareVersion"),
            serial_number=hydrotap.get("serialNumber"),
        )
        self._attr_options = description.options_fn()

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        settings = (self.coordinator.data.get("settings") or {}).get(
            self._hydrotap_id, {}
        )
        return self.entity_description.value_fn(settings)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        payload = self.entity_description.payload_fn(option)
        success = await self.coordinator.client.update_settings(
            self._hydrotap_id, payload
        )
        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(
                "Failed to set %s to %s for %s",
                self.entity_description.key,
                option,
                self._hydrotap_id,
            )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ZipAssist select entities from a config entry."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    hydrotaps: list[dict] = coordinator.data.get("hydrotaps", [])

    entities: list[ZipAssistSelect] = []
    for hydrotap in hydrotaps:
        hid = hydrotap.get("hydrotapId")
        if not hid:
            continue
        for description in SELECT_TYPES:
            entities.append(ZipAssistSelect(coordinator, hydrotap, description))

    _LOGGER.debug("Creating %d select entities", len(entities))
    async_add_entities(entities)