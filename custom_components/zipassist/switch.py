"""Switch platform for ZipAssist CMMS — safety toggles."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
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
class ZipAssistSwitchEntityDescription(SwitchEntityDescription):
    """Description for a ZipAssist switch entity."""

    value_fn: Callable[[dict], bool | None]
    available_fn: Callable[[dict], bool]  # whether the feature is available
    setting_key: str  # top-level key in the settings payload


SWITCH_TYPES: tuple[ZipAssistSwitchEntityDescription, ...] = (
    ZipAssistSwitchEntityDescription(
        key="safety_lock",
        translation_key="safety_lock",
        icon="mdi:lock",
        value_fn=lambda s: s.get("safetyLockEnabled"),
        available_fn=lambda so: so.get("safety", {}).get("safetyLockEnabled", False),
        setting_key="safetyLockEnabled",
    ),
    ZipAssistSwitchEntityDescription(
        key="hot_isolation",
        translation_key="hot_isolation",
        icon="mdi:water-off",
        value_fn=lambda s: s.get("hotIsolationEnabled"),
        available_fn=lambda so: so.get("safety", {}).get(
            "hotIsolationEnabled", False
        ),
        setting_key="hotIsolationEnabled",
    ),
)


class ZipAssistSwitch(CoordinatorEntity, SwitchEntity):
    """Switch entity for a ZipAssist hydrotap safety setting."""

    entity_description: ZipAssistSwitchEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        hydrotap: dict,
        description: ZipAssistSwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
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

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the safety feature on."""
        await self._set_setting(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the safety feature off."""
        await self._set_setting(False)

    async def _set_setting(self, value: bool) -> None:
        """Send the setting update to the API."""
        payload = {self.entity_description.setting_key: value}
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
    """Set up ZipAssist switch entities from a config entry."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    hydrotaps: list[dict] = coordinator.data.get("hydrotaps", [])
    settings_options_map: dict = coordinator.data.get("settings_options", {})

    entities: list[ZipAssistSwitch] = []
    for hydrotap in hydrotaps:
        hid = hydrotap.get("hydrotapId")
        if not hid:
            continue
        tap_options = settings_options_map.get(hid, {})
        for description in SWITCH_TYPES:
            if description.available_fn(tap_options):
                entities.append(
                    ZipAssistSwitch(coordinator, hydrotap, description)
                )

    _LOGGER.debug("Creating %d switch entities", len(entities))
    async_add_entities(entities)