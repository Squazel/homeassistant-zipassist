"""Number platform for ZipAssist CMMS — temperature controls."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
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
class ZipAssistNumberEntityDescription(NumberEntityDescription):
    """Description for a ZipAssist number entity."""

    value_fn: Callable[[dict], float | None]
    attr_fn: Callable[[dict], str]  # settings key path, e.g. "boiling" or "chilled"


NUMBER_TYPES: tuple[ZipAssistNumberEntityDescription, ...] = (
    ZipAssistNumberEntityDescription(
        key="boiling_temp",
        translation_key="boiling_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        value_fn=lambda s: (
            s.get("boiling", {}).get("temp")
            if s.get("boiling", {}).get("isFeature")
            else None
        ),
        attr_fn=lambda _: "boiling",
    ),
    ZipAssistNumberEntityDescription(
        key="chilled_temp",
        translation_key="chilled_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        value_fn=lambda s: (
            s.get("chilled", {}).get("temp")
            if s.get("chilled", {}).get("isFeature")
            else None
        ),
        attr_fn=lambda _: "chilled",
    ),
)


class ZipAssistNumber(CoordinatorEntity, NumberEntity):
    """Number entity for a ZipAssist hydrotap temperature setting."""

    entity_description: ZipAssistNumberEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        hydrotap: dict,
        description: ZipAssistNumberEntityDescription,
    ) -> None:
        """Initialize the number entity."""
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

        # Set min/max/step from settings-options if available
        self._set_range_from_options(coordinator.data)

    def _set_range_from_options(self, data: dict) -> None:
        """Set native_min/max/step from settings-options data."""
        options = (data.get("settings_options") or {}).get(self._hydrotap_id, {})
        water = options.get("water", {})
        attr = self.entity_description.attr_fn({})
        water_type = water.get(attr)
        if isinstance(water_type, dict):
            temp_opts = water_type.get("temp")
            if isinstance(temp_opts, dict):
                self._attr_native_min_value = float(temp_opts.get("min", 0))
                self._attr_native_max_value = float(temp_opts.get("max", 100))
                self._attr_native_step = float(temp_opts.get("step", 1))

    @property
    def native_value(self) -> float | None:
        """Return the current temperature."""
        settings = (self.coordinator.data.get("settings") or {}).get(
            self._hydrotap_id, {}
        )
        return self.entity_description.value_fn(settings)

    async def async_set_native_value(self, value: float) -> None:
        """Set the temperature via the API."""
        attr = self.entity_description.attr_fn({})
        payload = {attr: {"temp": value}}
        success = await self.coordinator.client.update_settings(
            self._hydrotap_id, payload
        )
        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to set %s temp for %s", attr, self._hydrotap_id)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ZipAssist number entities from a config entry."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    hydrotaps: list[dict] = coordinator.data.get("hydrotaps", [])
    settings_map: dict = coordinator.data.get("settings", {})

    entities: list[ZipAssistNumber] = []
    for hydrotap in hydrotaps:
        hid = hydrotap.get("hydrotapId")
        if not hid:
            continue
        tap_settings = settings_map.get(hid, {})
        for description in NUMBER_TYPES:
            # Only create if the feature is available (isFeature=true)
            if description.value_fn(tap_settings) is not None:
                entities.append(ZipAssistNumber(coordinator, hydrotap, description))

    _LOGGER.debug("Creating %d number entities", len(entities))
    async_add_entities(entities)