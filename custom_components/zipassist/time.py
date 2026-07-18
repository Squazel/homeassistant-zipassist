"""Time platform for ZipAssist CMMS — energy timer on/off times."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import time

from homeassistant.components.time import TimeEntity, TimeEntityDescription
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

_DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _parse_time(value: str | None) -> time | None:
    """Parse 'HH:MM:SS' string to time, or None."""
    if not value:
        return None
    parts = value.strip().split(":")
    try:
        return time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
    except (ValueError, IndexError):
        return None


def _format_time(t: time) -> str:
    """Format a time as 'HH:MM:SS'."""
    return t.strftime("%H:%M:%S")


@dataclass(frozen=True, kw_only=True)
class ZipAssistTimeEntityDescription(TimeEntityDescription):
    """Description for a ZipAssist time entity."""

    value_fn: Callable[[dict], str | None]
    available_fn: Callable[[dict], bool]
    payload_fn: Callable[[time], dict]


def _energy_time_payload(mode: str, slot: str, field: str):
    """Build payload for energy timer time settings.

    mode: "everyday" | "daily" | "weekdayWeekend"
    slot: day name for "daily", or "weekday"/"weekend" for weekdayWeekend
    field: "onTime" | "offTime"
    """
    if mode == "everyday":
        return lambda t: {"energy": {"everyday": {field: _format_time(t)}}}
    if mode == "daily":
        return lambda t: {"energy": {"daily": {slot: {field: _format_time(t)}}}}
    return lambda t: {"energy": {"weekdayWeekend": {slot: {field: _format_time(t)}}}}


def _energy_available(mode: str):
    """Return an available_fn that checks activeMode matches."""
    return lambda s: (s.get("energy") or {}).get("activeMode") == mode


TIME_TYPES: tuple[ZipAssistTimeEntityDescription, ...] = (
    # --- energy: everyday on/off times ---
    ZipAssistTimeEntityDescription(
        key="energy_everyday_on_time",
        translation_key="energy_everyday_on_time",
        icon="mdi:clock-start",
        value_fn=lambda s: (s.get("energy") or {}).get("everyday", {}).get("onTime"),
        available_fn=_energy_available("everyday"),
        payload_fn=_energy_time_payload("everyday", "", "onTime"),
    ),
    ZipAssistTimeEntityDescription(
        key="energy_everyday_off_time",
        translation_key="energy_everyday_off_time",
        icon="mdi:clock-end",
        value_fn=lambda s: (s.get("energy") or {}).get("everyday", {}).get("offTime"),
        available_fn=_energy_available("everyday"),
        payload_fn=_energy_time_payload("everyday", "", "offTime"),
    ),
    # --- energy: daily on/off times (7 days) ---
    *(
        ZipAssistTimeEntityDescription(
            key=f"energy_daily_{day}_on_time",
            translation_key=f"energy_daily_{day}_on_time",
            icon="mdi:clock-start",
            value_fn=lambda s, d=day: (s.get("energy") or {}).get("daily", {}).get(d, {}).get("onTime"),
            available_fn=_energy_available("daily"),
            payload_fn=_energy_time_payload("daily", day, "onTime"),
        )
        for day in _DAYS
    ),
    *(
        ZipAssistTimeEntityDescription(
            key=f"energy_daily_{day}_off_time",
            translation_key=f"energy_daily_{day}_off_time",
            icon="mdi:clock-end",
            value_fn=lambda s, d=day: (s.get("energy") or {}).get("daily", {}).get(d, {}).get("offTime"),
            available_fn=_energy_available("daily"),
            payload_fn=_energy_time_payload("daily", day, "offTime"),
        )
        for day in _DAYS
    ),
    # --- energy: weekday/weekend on/off times ---
    ZipAssistTimeEntityDescription(
        key="energy_weekday_on_time",
        translation_key="energy_weekday_on_time",
        icon="mdi:clock-start",
        value_fn=lambda s: (s.get("energy") or {}).get("weekdayWeekend", {}).get("weekday", {}).get("onTime"),
        available_fn=_energy_available("weekdayWeekend"),
        payload_fn=_energy_time_payload("weekdayWeekend", "weekday", "onTime"),
    ),
    ZipAssistTimeEntityDescription(
        key="energy_weekday_off_time",
        translation_key="energy_weekday_off_time",
        icon="mdi:clock-end",
        value_fn=lambda s: (s.get("energy") or {}).get("weekdayWeekend", {}).get("weekday", {}).get("offTime"),
        available_fn=_energy_available("weekdayWeekend"),
        payload_fn=_energy_time_payload("weekdayWeekend", "weekday", "offTime"),
    ),
    ZipAssistTimeEntityDescription(
        key="energy_weekend_on_time",
        translation_key="energy_weekend_on_time",
        icon="mdi:clock-start",
        value_fn=lambda s: (s.get("energy") or {}).get("weekdayWeekend", {}).get("weekend", {}).get("onTime"),
        available_fn=_energy_available("weekdayWeekend"),
        payload_fn=_energy_time_payload("weekdayWeekend", "weekend", "onTime"),
    ),
    ZipAssistTimeEntityDescription(
        key="energy_weekend_off_time",
        translation_key="energy_weekend_off_time",
        icon="mdi:clock-end",
        value_fn=lambda s: (s.get("energy") or {}).get("weekdayWeekend", {}).get("weekend", {}).get("offTime"),
        available_fn=_energy_available("weekdayWeekend"),
        payload_fn=_energy_time_payload("weekdayWeekend", "weekend", "offTime"),
    ),
)


class ZipAssistTime(CoordinatorEntity, TimeEntity):
    """Time entity for a ZipAssist hydrotap energy timer."""

    _attr_has_entity_name = True
    entity_description: ZipAssistTimeEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        hydrotap: dict,
        description: ZipAssistTimeEntityDescription,
    ) -> None:
        """Initialize the time entity."""
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
            serial_number=hydrotap.get("serialNumber"),
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> time | None:
        """Return the current time value."""
        settings = (self.coordinator.data.get("settings") or {}).get(
            self._hydrotap_id, {}
        )
        raw = self.entity_description.value_fn(settings)
        return _parse_time(raw)

    async def async_set_value(self, value: time) -> None:
        """Set the time value via the API."""
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
    """Set up ZipAssist time entities from a config entry."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    hydrotaps: list[dict] = coordinator.data.get("hydrotaps", [])
    settings_map: dict = coordinator.data.get("settings", {})

    entities: list[ZipAssistTime] = []
    for hydrotap in hydrotaps:
        hid = hydrotap.get("hydrotapId")
        if not hid:
            continue
        tap_settings = settings_map.get(hid, {})
        for description in TIME_TYPES:
            if description.available_fn(tap_settings):
                entities.append(ZipAssistTime(coordinator, hydrotap, description))

    _LOGGER.debug("Creating %d time entities", len(entities))
    async_add_entities(entities)