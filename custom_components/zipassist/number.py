"""Number platform for ZipAssist CMMS — temperature, filter, and dispense controls."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

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
    payload_fn: Callable[[float], dict]  # builds the PATCH payload from a value
    options_path: tuple[str, ...] = ()  # path in settings-options for range
    available_fn: Callable[[dict], bool] = lambda s: True  # whether to create entity


def _water_temp_payload(attr: str):
    """Build payload for water temperature settings."""
    return lambda v: {attr: {"temp": v}}


def _water_duration_payload(attr: str):
    """Build payload for water dispense duration settings."""
    return lambda v: {attr: {"duration": v}}


def _filter_payload(filter_type: str, field: str):
    """Build payload for filter limit settings."""
    return lambda v: {f"{filter_type}FilterLimits": {field: v}}


NUMBER_TYPES: tuple[ZipAssistNumberEntityDescription, ...] = (
    # --- temperature ---
    ZipAssistNumberEntityDescription(
        key="boiling_temp",
        translation_key="boiling_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        icon="mdi:thermometer-high",
        value_fn=lambda s: (
            s.get("boiling", {}).get("temp")
            if s.get("boiling", {}).get("isFeature")
            else None
        ),
        payload_fn=_water_temp_payload("boiling"),
        options_path=("water", "boiling", "temp"),
        available_fn=lambda s: s.get("boiling", {}).get("isFeature", False),
    ),
    ZipAssistNumberEntityDescription(
        key="chilled_temp",
        translation_key="chilled_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        icon="mdi:thermometer-low",
        value_fn=lambda s: (
            s.get("chilled", {}).get("temp")
            if s.get("chilled", {}).get("isFeature")
            else None
        ),
        payload_fn=_water_temp_payload("chilled"),
        options_path=("water", "chilled", "temp"),
        available_fn=lambda s: s.get("chilled", {}).get("isFeature", False),
    ),
    # --- dispense duration ---
    ZipAssistNumberEntityDescription(
        key="boiling_duration",
        translation_key="boiling_duration",
        native_unit_of_measurement="s",
        mode=NumberMode.BOX,
        icon="mdi:timer-outline",
        value_fn=lambda s: (
            s.get("boiling", {}).get("duration")
            if s.get("boiling", {}).get("isFeature")
            else None
        ),
        payload_fn=_water_duration_payload("boiling"),
        options_path=("water", "boiling", "duration"),
        available_fn=lambda s: s.get("boiling", {}).get("isFeature", False),
    ),
    ZipAssistNumberEntityDescription(
        key="chilled_duration",
        translation_key="chilled_duration",
        native_unit_of_measurement="s",
        mode=NumberMode.BOX,
        icon="mdi:timer-outline",
        value_fn=lambda s: (
            s.get("chilled", {}).get("duration")
            if s.get("chilled", {}).get("isFeature")
            else None
        ),
        payload_fn=_water_duration_payload("chilled"),
        options_path=("water", "chilled", "duration"),
        available_fn=lambda s: s.get("chilled", {}).get("isFeature", False),
    ),
    ZipAssistNumberEntityDescription(
        key="sparkling_duration",
        translation_key="sparkling_duration",
        native_unit_of_measurement="s",
        mode=NumberMode.BOX,
        icon="mdi:timer-outline",
        value_fn=lambda s: (
            s.get("sparkling", {}).get("duration")
            if s.get("sparkling", {}).get("isFeature")
            else None
        ),
        payload_fn=_water_duration_payload("sparkling"),
        options_path=("water", "sparkling", "duration"),
        available_fn=lambda s: s.get("sparkling", {}).get("isFeature", False),
    ),
    ZipAssistNumberEntityDescription(
        key="ambient_duration",
        translation_key="ambient_duration",
        native_unit_of_measurement="s",
        mode=NumberMode.BOX,
        icon="mdi:timer-outline",
        value_fn=lambda s: (
            s.get("ambient", {}).get("duration")
            if s.get("ambient", {}).get("isFeature")
            else None
        ),
        payload_fn=_water_duration_payload("ambient"),
        options_path=("water", "ambient", "duration"),
        available_fn=lambda s: s.get("ambient", {}).get("isFeature", False),
    ),
    # --- filter limits ---
    ZipAssistNumberEntityDescription(
        key="internal_filter_litres",
        translation_key="internal_filter_litres",
        native_unit_of_measurement="L",
        mode=NumberMode.BOX,
        icon="mdi:water-filter",
        value_fn=lambda s: (s.get("internalFilterLimits") or {}).get("litres"),
        payload_fn=_filter_payload("internal", "litres"),
        options_path=("filters", "internal", "litres"),
        available_fn=lambda s: (s.get("internalFilterLimits") or {}).get("litres")
        is not None,
    ),
    ZipAssistNumberEntityDescription(
        key="internal_filter_days",
        translation_key="internal_filter_days",
        native_unit_of_measurement="days",
        mode=NumberMode.BOX,
        icon="mdi:calendar-clock",
        value_fn=lambda s: (s.get("internalFilterLimits") or {}).get("days"),
        payload_fn=_filter_payload("internal", "days"),
        options_path=("filters", "internal", "days"),
        available_fn=lambda s: (s.get("internalFilterLimits") or {}).get("days")
        is not None,
    ),
    ZipAssistNumberEntityDescription(
        key="external_filter_litres",
        translation_key="external_filter_litres",
        native_unit_of_measurement="L",
        mode=NumberMode.BOX,
        icon="mdi:water-filter",
        value_fn=lambda s: (s.get("externalFilterLimits") or {}).get("litres"),
        payload_fn=_filter_payload("external", "litres"),
        options_path=("filters", "external", "litres"),
        available_fn=lambda s: (s.get("externalFilterLimits") or {}).get("litres")
        is not None,
    ),
    ZipAssistNumberEntityDescription(
        key="external_filter_days",
        translation_key="external_filter_days",
        native_unit_of_measurement="days",
        mode=NumberMode.BOX,
        icon="mdi:calendar-clock",
        value_fn=lambda s: (s.get("externalFilterLimits") or {}).get("days"),
        payload_fn=_filter_payload("external", "days"),
        options_path=("filters", "external", "days"),
        available_fn=lambda s: (s.get("externalFilterLimits") or {}).get("days")
        is not None,
    ),
)


class ZipAssistNumber(CoordinatorEntity, NumberEntity):
    """Number entity for a ZipAssist hydrotap setting."""

    _attr_has_entity_name = True
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
        self._attr_unique_id = f"zipassist_{self._hydrotap_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._hydrotap_id)},
            name=device_name(hydrotap),
            manufacturer="Zip Industries",
            model=hydrotap.get("moduleName"),
            sw_version=hydrotap.get("firmwareVersion"),
            serial_number=str(hydrotap.get("serialNumber", "")),
        )

        # Set min/max/step from settings-options if available
        self._set_range_from_options(coordinator.data)

    def _set_range_from_options(self, data: dict) -> None:
        """Set native_min/max/step from settings-options data."""
        options = (data.get("settings_options") or {}).get(self._hydrotap_id, {})
        # Walk the options_path to find the range dict
        current: dict = options
        for key in self.entity_description.options_path:
            if isinstance(current, dict):
                current = current.get(key, {})
            else:
                current = {}
        if isinstance(current, dict) and "min" in current:
            self._attr_native_min_value = float(current.get("min", 0))
            self._attr_native_max_value = float(current.get("max", 100))
            self._attr_native_step = float(current.get("step", 1))

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self.coordinator.last_update_success)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return integration marker for frontend card discovery."""
        return {"integration": DOMAIN}

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        settings = (self.coordinator.data.get("settings") or {}).get(
            self._hydrotap_id, {}
        )
        return self.entity_description.value_fn(settings)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value via the API."""
        payload = self.entity_description.payload_fn(value)
        success = await self.coordinator.client.update_settings(
            self._hydrotap_id, payload
        )
        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(
                "Failed to set %s for %s", self.entity_description.key, self._hydrotap_id
            )


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
            if description.available_fn(tap_settings):
                entities.append(ZipAssistNumber(coordinator, hydrotap, description))

    _LOGGER.debug("Creating %d number entities", len(entities))
    async_add_entities(entities)