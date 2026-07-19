"""Switch platform for ZipAssist CMMS — safety toggles and energy timer actives."""

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

# Days of the week for daily energy schedule
_DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


@dataclass(frozen=True, kw_only=True)
class ZipAssistSwitchEntityDescription(SwitchEntityDescription):
    """Description for a ZipAssist switch entity."""

    value_fn: Callable[[dict], bool | None]
    available_fn: Callable[[dict], bool]  # whether the feature is available
    payload_fn: Callable[[bool], dict]  # builds the PATCH payload from a bool


def _safety_payload(key: str):
    """Build payload for safety toggles."""
    return lambda v: {key: v}


def _energy_active_payload(mode: str, slot: str, field: str):
    """Build payload for energy timer active toggles.

    mode: "everyday" | "daily" | "weekdayWeekend"
    slot: day name for "daily", or "weekday"/"weekend" for weekdayWeekend
    field: "onTimeActive" | "offTimeActive"
    """
    if mode == "everyday":
        return lambda v: {"energy": {"everyday": {field: v}}}
    if mode == "daily":
        return lambda v: {"energy": {"daily": {slot: {field: v}}}}
    # weekdayWeekend
    return lambda v: {"energy": {"weekdayWeekend": {slot: {field: v}}}}


def _energy_available(mode: str):
    """Return an available_fn that checks activeMode matches."""
    return lambda s: (s.get("energy") or {}).get("activeMode") == mode


SWITCH_TYPES: tuple[ZipAssistSwitchEntityDescription, ...] = (
    # --- safety toggles ---
    ZipAssistSwitchEntityDescription(
        key="safety_lock",
        translation_key="safety_lock",
        icon="mdi:lock",
        value_fn=lambda s: s.get("safetyLockEnabled"),
        available_fn=lambda so: so.get("safety", {}).get("safetyLockEnabled", False),
        payload_fn=_safety_payload("safetyLockEnabled"),
    ),
    ZipAssistSwitchEntityDescription(
        key="hot_isolation",
        translation_key="hot_isolation",
        icon="mdi:water-off",
        value_fn=lambda s: s.get("hotIsolationEnabled"),
        available_fn=lambda so: so.get("safety", {}).get(
            "hotIsolationEnabled", False
        ),
        payload_fn=_safety_payload("hotIsolationEnabled"),
    ),
    # --- energy: everyday on/off active ---
    ZipAssistSwitchEntityDescription(
        key="energy_everyday_on_active",
        translation_key="energy_everyday_on_active",
        icon="mdi:timer-play-outline",
        value_fn=lambda s: (s.get("energy") or {}).get("everyday", {}).get("onTimeActive"),
        available_fn=_energy_available("everyday"),
        payload_fn=_energy_active_payload("everyday", "", "onTimeActive"),
    ),
    ZipAssistSwitchEntityDescription(
        key="energy_everyday_off_active",
        translation_key="energy_everyday_off_active",
        icon="mdi:timer-stop-outline",
        value_fn=lambda s: (s.get("energy") or {}).get("everyday", {}).get("offTimeActive"),
        available_fn=_energy_available("everyday"),
        payload_fn=_energy_active_payload("everyday", "", "offTimeActive"),
    ),
    # --- energy: daily on/off active (7 days) ---
    *(
        ZipAssistSwitchEntityDescription(
            key=f"energy_daily_{day}_on_active",
            translation_key=f"energy_daily_{day}_on_active",
            icon="mdi:timer-play-outline",
            value_fn=lambda s, d=day: (s.get("energy") or {}).get("daily", {}).get(d, {}).get("onTimeActive"),
            available_fn=_energy_available("daily"),
            payload_fn=_energy_active_payload("daily", day, "onTimeActive"),
        )
        for day in _DAYS
    ),
    *(
        ZipAssistSwitchEntityDescription(
            key=f"energy_daily_{day}_off_active",
            translation_key=f"energy_daily_{day}_off_active",
            icon="mdi:timer-stop-outline",
            value_fn=lambda s, d=day: (s.get("energy") or {}).get("daily", {}).get(d, {}).get("offTimeActive"),
            available_fn=_energy_available("daily"),
            payload_fn=_energy_active_payload("daily", day, "offTimeActive"),
        )
        for day in _DAYS
    ),
    # --- energy: weekday/weekend on/off active ---
    ZipAssistSwitchEntityDescription(
        key="energy_weekday_on_active",
        translation_key="energy_weekday_on_active",
        icon="mdi:timer-play-outline",
        value_fn=lambda s: (s.get("energy") or {}).get("weekdayWeekend", {}).get("weekday", {}).get("onTimeActive"),
        available_fn=_energy_available("weekdayWeekend"),
        payload_fn=_energy_active_payload("weekdayWeekend", "weekday", "onTimeActive"),
    ),
    ZipAssistSwitchEntityDescription(
        key="energy_weekday_off_active",
        translation_key="energy_weekday_off_active",
        icon="mdi:timer-stop-outline",
        value_fn=lambda s: (s.get("energy") or {}).get("weekdayWeekend", {}).get("weekday", {}).get("offTimeActive"),
        available_fn=_energy_available("weekdayWeekend"),
        payload_fn=_energy_active_payload("weekdayWeekend", "weekday", "offTimeActive"),
    ),
    ZipAssistSwitchEntityDescription(
        key="energy_weekend_on_active",
        translation_key="energy_weekend_on_active",
        icon="mdi:timer-play-outline",
        value_fn=lambda s: (s.get("energy") or {}).get("weekdayWeekend", {}).get("weekend", {}).get("onTimeActive"),
        available_fn=_energy_available("weekdayWeekend"),
        payload_fn=_energy_active_payload("weekdayWeekend", "weekend", "onTimeActive"),
    ),
    ZipAssistSwitchEntityDescription(
        key="energy_weekend_off_active",
        translation_key="energy_weekend_off_active",
        icon="mdi:timer-stop-outline",
        value_fn=lambda s: (s.get("energy") or {}).get("weekdayWeekend", {}).get("weekend", {}).get("offTimeActive"),
        available_fn=_energy_available("weekdayWeekend"),
        payload_fn=_energy_active_payload("weekdayWeekend", "weekend", "offTimeActive"),
    ),
)


class ZipAssistSwitch(CoordinatorEntity, SwitchEntity):
    """Switch entity for a ZipAssist hydrotap setting."""

    _attr_has_entity_name = True
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

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return integration marker for frontend card discovery."""
        return {"integration": DOMAIN}

    @property
    def is_on(self) -> bool | None:
        """Return true if the setting is enabled."""
        settings = (self.coordinator.data.get("settings") or {}).get(
            self._hydrotap_id, {}
        )
        return self.entity_description.value_fn(settings)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the setting on."""
        await self._set_setting(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the setting off."""
        await self._set_setting(False)

    async def _set_setting(self, value: bool) -> None:
        """Send the setting update to the API."""
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
            # Safety switches use settings_options to check feature availability
            if not description.key.startswith("energy_"):
                if not description.available_fn(tap_options):
                    continue
            entities.append(
                ZipAssistSwitch(coordinator, hydrotap, description)
            )

    _LOGGER.debug("Creating %d switch entities", len(entities))
    async_add_entities(entities)