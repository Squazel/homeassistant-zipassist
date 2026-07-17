"""Sensor platform for ZipAssist CMMS."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
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
        value_fn=lambda h: h.get("filterLifeRemainingLitres"),
    ),
    ZipAssistSensorEntityDescription(
        key="filter_days_remaining",
        translation_key="filter_days_remaining",
        native_unit_of_measurement="days",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda h: h.get("filterLifeRemainingDays"),
    ),
    ZipAssistSensorEntityDescription(
        key="filter_estimated_days",
        translation_key="filter_estimated_days",
        native_unit_of_measurement="days",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda h: h.get("filterLifeRemainingEstimated"),
    ),
    ZipAssistSensorEntityDescription(
        key="average_daily_usage",
        translation_key="average_daily_usage",
        native_unit_of_measurement="L/day",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda h: h.get("averageDailyUsage"),
    ),
    ZipAssistSensorEntityDescription(
        key="peak_hourly_usage",
        translation_key="peak_hourly_usage",
        native_unit_of_measurement="L/h",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda h: h.get("peakHourlyUsage"),
    ),
    ZipAssistSensorEntityDescription(
        key="last_sync",
        translation_key="last_sync",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda h: h.get("lastSyncTimestamp"),
    ),
    ZipAssistSensorEntityDescription(
        key="status",
        translation_key="status",
        value_fn=lambda h: h.get("status"),
    ),
    ZipAssistSensorEntityDescription(
        key="serial_number",
        translation_key="serial_number",
        value_fn=lambda h: h.get("serialNumber"),
    ),
    ZipAssistSensorEntityDescription(
        key="firmware_version",
        translation_key="firmware_version",
        value_fn=lambda h: h.get("firmwareVersion"),
    ),
    ZipAssistSensorEntityDescription(
        key="system_fault_details",
        translation_key="system_fault_details",
        icon="mdi:alert-circle",
        value_fn=lambda h: None,  # overridden in the entity — uses faults dict
    ),
)


class ZipAssistSensor(CoordinatorEntity, SensorEntity):
    """Sensor for a ZipAssist hydrotap."""

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
    def native_value(self) -> str | int | float | None:
        """Return the state of the sensor."""
        if self.entity_description.key == "system_fault_details":
            faults = (self.coordinator.data.get("faults") or {}).get(
                self._hydrotap_id, []
            )
            if not faults:
                return "No faults"
            # Return comma-separated fault descriptions
            return ", ".join(
                f.get("faultCode", f.get("code", "Unknown"))
                for f in faults
            )
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