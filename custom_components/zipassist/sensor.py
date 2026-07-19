"""Sensor platform for ZipAssist CMMS."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfVolume
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
class ZipAssistSensorEntityDescription(SensorEntityDescription):
    """Description for a ZipAssist sensor entity."""

    value_fn: Callable[[dict], str | int | float | None]


SENSOR_TYPES: tuple[ZipAssistSensorEntityDescription, ...] = (
    ZipAssistSensorEntityDescription(
        key="filter_litres_remaining",
        translation_key="filter_litres_remaining",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-opacity",
        value_fn=lambda h: h.get("filterLifeRemainingLitres"),
    ),
    ZipAssistSensorEntityDescription(
        key="filter_days_remaining",
        translation_key="filter_days_remaining",
        native_unit_of_measurement="days",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:calendar-clock",
        value_fn=lambda h: h.get("filterLifeRemainingDays"),
    ),
    ZipAssistSensorEntityDescription(
        key="filter_estimated_days",
        translation_key="filter_estimated_days",
        native_unit_of_measurement="days",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:calendar-sync",
        value_fn=lambda h: h.get("filterLifeRemainingEstimated"),
    ),
    ZipAssistSensorEntityDescription(
        key="average_daily_usage",
        translation_key="average_daily_usage",
        native_unit_of_measurement="L/day",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-percent",
        value_fn=lambda h: h.get("averageDailyUsage"),
    ),
    ZipAssistSensorEntityDescription(
        key="peak_hourly_usage",
        translation_key="peak_hourly_usage",
        native_unit_of_measurement="L/h",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-sync",
        value_fn=lambda h: h.get("peakHourlyUsage"),
    ),
    ZipAssistSensorEntityDescription(
        key="last_sync",
        translation_key="last_sync",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda h: h.get("lastSyncTimestamp"),
    ),
    ZipAssistSensorEntityDescription(
        key="status",
        translation_key="status",
        icon="mdi:information-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda h: h.get("status"),
    ),
    ZipAssistSensorEntityDescription(
        key="serial_number",
        translation_key="serial_number",
        icon="mdi:numeric",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda h: h.get("serialNumber"),
    ),
    ZipAssistSensorEntityDescription(
        key="firmware_version",
        translation_key="firmware_version",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda h: h.get("firmwareVersion"),
    ),
    ZipAssistSensorEntityDescription(
        key="system_fault_details",
        translation_key="system_fault_details",
        icon="mdi:alert-circle",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda h: None,  # overridden in the entity — uses faults dict
    ),
    # --- status log sensors ---
    ZipAssistSensorEntityDescription(
        key="wifi_signal_strength",
        translation_key="wifi_signal_strength",
        native_unit_of_measurement="dBm",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda h: None,  # overridden — uses status_logs
    ),
    ZipAssistSensorEntityDescription(
        key="energy_since_last_log",
        translation_key="energy_since_last_log",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda h: None,
    ),
    ZipAssistSensorEntityDescription(
        key="energy_total",
        translation_key="energy_total",
        native_unit_of_measurement="kWh",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda h: None,
    ),
    ZipAssistSensorEntityDescription(
        key="sleep_mode_status",
        translation_key="sleep_mode_status",
        icon="mdi:sleep",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda h: None,
    ),
    ZipAssistSensorEntityDescription(
        key="litres_filtered_internal",
        translation_key="litres_filtered_internal",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:water-filter",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda h: None,
    ),
    ZipAssistSensorEntityDescription(
        key="litres_filtered_external",
        translation_key="litres_filtered_external",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:water-filter",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda h: None,
    ),
    ZipAssistSensorEntityDescription(
        key="days_filtered_internal",
        translation_key="days_filtered_internal",
        native_unit_of_measurement="days",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:calendar-check",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda h: None,
    ),
    ZipAssistSensorEntityDescription(
        key="days_filtered_external",
        translation_key="days_filtered_external",
        native_unit_of_measurement="days",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:calendar-check",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda h: None,
    ),
)


def _parse_timestamp(raw: str) -> datetime | None:
    """Parse an ISO 8601 timestamp string into a datetime.

    Handles formats like '2026-07-19T05:22:00+0000' (no colon in tz offset).
    """
    if not raw:
        return None
    try:
        # Handle +0000 / -0500 offset format (missing colon)
        if len(raw) >= 5 and raw[-5] in ("+", "-") and raw[-3] != ":":
            raw = raw[:-2] + ":" + raw[-2:]
        return datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        _LOGGER.debug("Could not parse timestamp: %s", raw)
        return None


class ZipAssistSensor(CoordinatorEntity, SensorEntity):
    """Sensor for a ZipAssist hydrotap."""

    _attr_has_entity_name = True
    entity_description: ZipAssistSensorEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        hydrotap: dict,
        description: ZipAssistSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
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

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    def _resolve_sleep_mode_name(self, code: int | str | None) -> str | None:
        """Resolve a numeric sleep mode code to a human-readable name.

        Uses the sleep_modes list fetched by the coordinator from
        /api/sleep-modes. Falls back to the raw code if no match is found.
        """
        if code is None:
            return None
        sleep_modes = self.coordinator.data.get("sleep_modes") or []
        for mode in sleep_modes:
            mode_code = mode.get("code", mode.get("sleepModeCode", mode.get("id")))
            if str(mode_code) == str(code):
                return mode.get("name", str(code))
        return str(code)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes for rich data."""
        attrs: dict[str, Any] = {}

        # Find the hydrotap in the list
        hydrotap: dict[str, Any] | None = None
        for h in self.coordinator.data.get("hydrotaps", []):
            if h.get("hydrotapId") == self._hydrotap_id:
                hydrotap = h
                break

        settings = (self.coordinator.data.get("settings") or {}).get(
            self._hydrotap_id, {}
        )
        status_log = (self.coordinator.data.get("status_logs") or {}).get(
            self._hydrotap_id, {}
        )
        faults = (self.coordinator.data.get("faults") or {}).get(
            self._hydrotap_id, []
        )

        key = self.entity_description.key

        # Filter sensors: include filter limits from settings
        if key in (
            "filter_litres_remaining",
            "filter_days_remaining",
            "filter_estimated_days",
        ):
            internal = settings.get("internalFilterLimits", {})
            external = settings.get("externalFilterLimits", {})
            if internal:
                attrs["internal_filter_limit_litres"] = internal.get("litres")
                attrs["internal_filter_limit_days"] = internal.get("days")
            if external:
                attrs["external_filter_limit_litres"] = external.get("litres")
                attrs["external_filter_limit_days"] = external.get("days")

        # System fault details: include full fault objects
        if key == "system_fault_details" and faults:
            attrs["faults"] = faults

        # Status log sensors: include related status log fields
        if key in (
            "wifi_signal_strength",
            "energy_since_last_log",
            "energy_total",
            "sleep_mode_status",
            "litres_filtered_internal",
            "litres_filtered_external",
            "days_filtered_internal",
            "days_filtered_external",
        ):
            if status_log:
                attrs["log_timestamp"] = status_log.get("timestamp")
                attrs["time_since_last_log"] = status_log.get("timeSinceLastLog")
                attrs["hydrotap_active"] = status_log.get("hydrotapActive")

        # Sleep mode: expose raw code as attribute
        if key == "sleep_mode_status" and status_log:
            attrs["sleep_mode_code"] = status_log.get("sleepModeStatus")

        # Hydrotap list sensors: include location and permissions
        if hydrotap and key in (
            "filter_litres_remaining",
            "filter_days_remaining",
            "filter_estimated_days",
            "average_daily_usage",
            "peak_hourly_usage",
            "last_sync",
            "status",
        ):
            attrs["building_name"] = hydrotap.get("buildingName")
            attrs["level"] = hydrotap.get("level")
            attrs["location_in_building"] = hydrotap.get("locationInBuilding")
            attrs["zip_managed"] = hydrotap.get("zipManaged")
            permissions = hydrotap.get("permissions", {})
            if permissions:
                attrs["can_view"] = permissions.get("view")
                attrs["can_edit"] = permissions.get("edit")

        return attrs or None

    @property
    def native_value(self) -> str | int | float | datetime | None:
        """Return the state of the sensor."""
        key = self.entity_description.key

        # system_fault_details uses faults dict
        if key == "system_fault_details":
            faults = (self.coordinator.data.get("faults") or {}).get(
                self._hydrotap_id, []
            )
            if not faults:
                return "No faults"
            return ", ".join(
                f.get("faultCode", f.get("code", "Unknown"))
                for f in faults
            )

        # last_sync: convert ISO 8601 string to datetime for TIMESTAMP device class
        if key == "last_sync":
            for h in self.coordinator.data.get("hydrotaps", []):
                if h.get("hydrotapId") == self._hydrotap_id:
                    raw = h.get("lastSyncTimestamp")
                    if raw:
                        return _parse_timestamp(raw)
                    return None
            return None

        # Status log sensors use the status_logs dict
        status_log = (self.coordinator.data.get("status_logs") or {}).get(
            self._hydrotap_id, {}
        )
        status_log_map = {
            "wifi_signal_strength": lambda l: l.get("wifiSignalStrength"),
            "energy_since_last_log": lambda l: l.get("energyKwhSinceLastLog"),
            "energy_total": lambda l: l.get("energyKwhTotal"),
            "sleep_mode_status": lambda l: self._resolve_sleep_mode_name(
                l.get("sleepModeStatus")
            ),
            "litres_filtered_internal": lambda l: l.get("litresFilteredInternal"),
            "litres_filtered_external": lambda l: l.get("litresFilteredExternal"),
            "days_filtered_internal": lambda l: l.get("daysFilteredInternal"),
            "days_filtered_external": lambda l: l.get("daysFilteredExternal"),
        }
        if key in status_log_map:
            return status_log_map[key](status_log)

        # Default: look up in hydrotaps list
        for h in self.coordinator.data.get("hydrotaps", []):
            if h.get("hydrotapId") == self._hydrotap_id:
                return self.entity_description.value_fn(h)
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ZipAssist sensors from a config entry."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    hydrotaps: list[dict] = coordinator.data.get("hydrotaps", [])

    entities: list[ZipAssistSensor] = []
    for hydrotap in hydrotaps:
        for description in SENSOR_TYPES:
            entities.append(ZipAssistSensor(coordinator, hydrotap, description))

    _LOGGER.debug("Creating %d sensors for %d hydrotaps", len(entities), len(hydrotaps))
    async_add_entities(entities)