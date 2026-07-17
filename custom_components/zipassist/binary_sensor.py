"""Binary sensor platform for ZipAssist CMMS — safety toggles."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
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


@dataclass(frozen=True, kw_only=True)
class ZipAssistBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Description for a ZipAssist binary sensor entity."""

    value_fn: Callable[[dict], bool | None]
    available_fn: Callable[[dict], bool]  # whether the feature is available


BINARY_SENSOR_TYPES: tuple[ZipAssistBinarySensorEntityDescription, ...] = (
    ZipAssistBinarySensorEntityDescription(
        key="safety_lock",
        translation_key="safety_lock",
        value_fn=lambda s: s.get("safetyLockEnabled"),
        available_fn=lambda so: so.get("safety", {}).get("safetyLockEnabled", False),
    ),
    ZipAssistBinarySensorEntityDescription(
        key="hot_isolation",
        translation_key="hot_isolation",
        value_fn=lambda s: s.get("hotIsolationEnabled"),
        available_fn=lambda so: so.get("safety", {}).get(
            "hotIsolationEnabled", False
        ),
    ),
)


class ZipAssistBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for a ZipAssist hydrotap safety setting."""

    entity_description: ZipAssistBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        hydrotap: dict,
        description: ZipAssistBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
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

    @property
    def is_on(self) -> bool | None:
        """Return true if the safety feature is enabled."""
        settings = (self.coordinator.data.get("settings") or {}).get(
            self._hydrotap_id, {}
        )
        return self.entity_description.value_fn(settings)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ZipAssist binary sensor entities from a config entry."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    hydrotaps: list[dict] = coordinator.data.get("hydrotaps", [])
    settings_options_map: dict = coordinator.data.get("settings_options", {})

    entities: list[ZipAssistBinarySensor] = []
    for hydrotap in hydrotaps:
        hid = hydrotap.get("hydrotapId")
        if not hid:
            continue
        tap_options = settings_options_map.get(hid, {})
        for description in BINARY_SENSOR_TYPES:
            # Only create if the feature is available per settings-options
            if description.available_fn(tap_options):
                entities.append(
                    ZipAssistBinarySensor(coordinator, hydrotap, description)
                )

    _LOGGER.debug("Creating %d binary sensor entities", len(entities))
    async_add_entities(entities)