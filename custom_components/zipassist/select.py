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

# Sleep mode codes from the API (fallback when API fetch fails)
_SLEEP_MODE_FALLBACK: list[str] = [
    "0", "1", "2", "3", "4", "5", "6", "7", "8",
]

ENERGY_MODE_OPTIONS: list[str] = [
    "everyday",
    "daily",
    "weekdayWeekend",
]

# Sync period: 10–60 min, step 10 min (stored as "HH:MM:SS")
SYNC_PERIOD_OPTIONS: list[str] = [
    "00:10:00", "00:20:00", "00:30:00", "00:40:00", "00:50:00", "01:00:00",
]


def _sleep_mode_options() -> list[str]:
    """Return hardcoded fallback sleep mode options."""
    return _SLEEP_MODE_FALLBACK


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


def _sync_period_payload(value: str) -> dict:
    return {"syncPeriod": value}


def _build_sleep_mode_options(coordinator_data: dict | None) -> list[str]:
    """Build sleep mode options from coordinator data or fallback."""
    if coordinator_data:
        sleep_modes = coordinator_data.get("sleep_modes")
        if isinstance(sleep_modes, list) and sleep_modes:
            # API returns list of dicts with code/name; extract codes as strings
            codes: list[str] = []
            for mode in sleep_modes:
                code = mode.get("code", mode.get("sleepModeCode", mode.get("id")))
                if code is not None:
                    codes.append(str(code))
            if codes:
                return codes
    return _SLEEP_MODE_FALLBACK


SELECT_TYPES: tuple[ZipAssistSelectEntityDescription, ...] = (
    ZipAssistSelectEntityDescription(
        key="sleep_mode",
        translation_key="sleep_mode",
        icon="mdi:sleep",
        value_fn=lambda s: str(s.get("sleepModeCode", "")),
        options_fn=lambda: _SLEEP_MODE_FALLBACK,  # overridden dynamically in entity
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
    ZipAssistSelectEntityDescription(
        key="sync_period",
        translation_key="sync_period",
        icon="mdi:sync",
        value_fn=lambda s: s.get("syncPeriod", ""),
        options_fn=lambda: SYNC_PERIOD_OPTIONS,
        payload_fn=_sync_period_payload,
    ),
)


class ZipAssistSelect(CoordinatorEntity, SelectEntity):
    """Select entity for a ZipAssist hydrotap setting."""

    _attr_has_entity_name = True
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
        self._attr_unique_id = f"zipassist_{self._hydrotap_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._hydrotap_id)},
            name=device_name(hydrotap),
            manufacturer="Zip Industries",
            model=hydrotap.get("moduleName"),
            sw_version=hydrotap.get("firmwareVersion"),
            serial_number=hydrotap.get("serialNumber"),
        )
        self._update_options()

    def _update_options(self) -> None:
        """Update options, using coordinator data for sleep modes."""
        if self.entity_description.key == "sleep_mode":
            self._attr_options = _build_sleep_mode_options(self.coordinator.data)
        else:
            self._attr_options = self.entity_description.options_fn()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_options()
        super()._handle_coordinator_update()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

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