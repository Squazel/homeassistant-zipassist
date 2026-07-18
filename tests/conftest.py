"""Shared fixtures for ZipAssist tests."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

# ------------------------------------------------------------------ HA stubs


@dataclass(frozen=True)
class _StubSensorEntityDescription:
    """Stub for SensorEntityDescription."""
    key: str = ""
    translation_key: str | None = None
    native_unit_of_measurement: str | None = None
    state_class: str | None = None
    device_class: str | None = None
    icon: str | None = None
    entity_category: str | None = None


@dataclass(frozen=True)
class _StubNumberEntityDescription:
    """Stub for NumberEntityDescription."""
    key: str = ""
    translation_key: str | None = None
    native_unit_of_measurement: str | None = None
    native_min_value: float = 0
    native_max_value: float = 100
    native_step: float = 1
    mode: str = "box"
    icon: str | None = None


@dataclass(frozen=True)
class _StubBinarySensorEntityDescription:
    """Stub for BinarySensorEntityDescription."""
    key: str = ""
    translation_key: str | None = None
    device_class: object = None
    icon: str | None = None


@dataclass(frozen=True)
class _StubSwitchEntityDescription:
    """Stub for SwitchEntityDescription."""
    key: str = ""
    translation_key: str | None = None
    icon: str | None = None


@dataclass(frozen=True)
class _StubSelectEntityDescription:
    """Stub for SelectEntityDescription."""
    key: str = ""
    translation_key: str | None = None
    icon: str | None = None


@dataclass(frozen=True)
class _StubTimeEntityDescription:
    """Stub for TimeEntityDescription."""
    key: str = ""
    translation_key: str | None = None
    icon: str | None = None


class _StubEntity:
    """Stub base for all HA entities that supports _attr_* pattern."""

    def __init__(self, *args, **kwargs):
        self._attr_unique_id: str | None = None
        self._attr_device_info: dict | None = None
        self._attr_native_min_value: float | None = None
        self._attr_native_max_value: float | None = None
        self._attr_native_step: float | None = None
        self._attr_native_unit_of_measurement: str | None = None

    @property
    def unique_id(self):
        return self._attr_unique_id

    @unique_id.setter
    def unique_id(self, value):
        self._attr_unique_id = value

    @property
    def device_info(self):
        return self._attr_device_info

    @device_info.setter
    def device_info(self, value):
        self._attr_device_info = value

    @property
    def native_min_value(self):
        return self._attr_native_min_value

    @native_min_value.setter
    def native_min_value(self, value):
        self._attr_native_min_value = value

    @property
    def native_max_value(self):
        return self._attr_native_max_value

    @native_max_value.setter
    def native_max_value(self, value):
        self._attr_native_max_value = value

    @property
    def native_step(self):
        return self._attr_native_step

    @native_step.setter
    def native_step(self, value):
        self._attr_native_step = value

    @property
    def native_unit_of_measurement(self):
        return self._attr_native_unit_of_measurement

    @native_unit_of_measurement.setter
    def native_unit_of_measurement(self, value):
        self._attr_native_unit_of_measurement = value


class _StubCoordinatorEntity(_StubEntity):
    """Stub for CoordinatorEntity."""

    def __init__(self, coordinator, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.coordinator = coordinator


class _StubSensorEntity(_StubEntity):
    """Stub for SensorEntity."""
    entity_description = None


class _StubNumberEntity(_StubEntity):
    """Stub for NumberEntity."""
    entity_description = None


class _StubBinarySensorEntity(_StubEntity):
    """Stub for BinarySensorEntity."""
    entity_description = None


class _StubSwitchEntity(_StubEntity):
    """Stub for SwitchEntity."""
    entity_description = None


class _StubSelectEntity(_StubEntity):
    """Stub for SelectEntity."""
    entity_description = None
    _attr_options: list[str] = []
    _attr_current_option: str | None = None

    @property
    def options(self):
        return self._attr_options

    @options.setter
    def options(self, value):
        self._attr_options = value

    @property
    def current_option(self):
        return self._attr_current_option

    @current_option.setter
    def current_option(self, value):
        self._attr_current_option = value


class _StubTimeEntity(_StubEntity):
    """Stub for TimeEntity."""
    entity_description = None


class _StubDataUpdateCoordinator:
    """Stub for DataUpdateCoordinator."""

    def __init__(self, hass, logger, *, name, update_interval, **kwargs):
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval
        self.data: dict = {}
        self.last_update_success: bool = True


class _StubUpdateFailed(Exception):
    """Stub for UpdateFailed."""


def _make_module(**attrs):
    m = MagicMock()
    m.configure_mock(**attrs)
    return m


# Register all HA stubs in sys.modules
sys.modules["homeassistant"] = MagicMock()
sys.modules["homeassistant.core"] = _make_module(HomeAssistant=MagicMock)
sys.modules["homeassistant.const"] = _make_module(
    UnitOfVolume=_make_module(LITERS="L"),
    UnitOfTemperature=_make_module(CELSIUS="°C"),
    CONF_EMAIL="email",
    CONF_PASSWORD="password",
)
class _StubConfigFlow:
    """Stub for ConfigFlow that supports domain kwarg."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        for k, v in kwargs.items():
            setattr(cls, k, v)

    def __init__(self, *args, **kwargs):
        pass

    async def async_set_unique_id(self, unique_id: str) -> None:
        """Stub."""
        pass

    def _abort_if_unique_id_configured(self) -> None:
        """Stub."""
        pass

    async def async_create_entry(self, **kwargs):
        """Stub."""
        pass

    async def async_show_form(self, **kwargs):
        """Stub."""
        pass


sys.modules["homeassistant.config_entries"] = _make_module(
    ConfigEntry=MagicMock, ConfigFlow=_StubConfigFlow, ConfigFlowResult=dict
)
sys.modules["homeassistant.helpers.entity"] = _make_module(DeviceInfo=dict)
sys.modules["homeassistant.helpers.entity_platform"] = _make_module(
    AddEntitiesCallback=MagicMock
)
sys.modules["homeassistant.helpers.config_validation"] = _make_module(
    config_entry_only_config_schema=lambda d: {},
)
sys.modules["homeassistant.helpers.update_coordinator"] = _make_module(
    CoordinatorEntity=_StubCoordinatorEntity,
    DataUpdateCoordinator=_StubDataUpdateCoordinator,
    UpdateFailed=_StubUpdateFailed,
)
sys.modules["homeassistant.helpers"] = MagicMock()
sys.modules["homeassistant.components.sensor"] = _make_module(
    SensorEntity=_StubSensorEntity,
    SensorEntityDescription=_StubSensorEntityDescription,
    SensorDeviceClass=_make_module(TIMESTAMP="timestamp"),
    SensorStateClass=_make_module(MEASUREMENT="measurement"),
)
sys.modules["homeassistant.components.number"] = _make_module(
    NumberEntity=_StubNumberEntity,
    NumberEntityDescription=_StubNumberEntityDescription,
    NumberMode=_make_module(BOX="box"),
)
sys.modules["homeassistant.components.binary_sensor"] = _make_module(
    BinarySensorEntity=_StubBinarySensorEntity,
    BinarySensorEntityDescription=_StubBinarySensorEntityDescription,
    BinarySensorDeviceClass=_make_module(PROBLEM=_make_module(value="problem")),
)
sys.modules["homeassistant.components.switch"] = _make_module(
    SwitchEntity=_StubSwitchEntity,
    SwitchEntityDescription=_StubSwitchEntityDescription,
)
sys.modules["homeassistant.components.select"] = _make_module(
    SelectEntity=_StubSelectEntity,
    SelectEntityDescription=_StubSelectEntityDescription,
)
sys.modules["homeassistant.components.time"] = _make_module(
    TimeEntity=_StubTimeEntity,
    TimeEntityDescription=_StubTimeEntityDescription,
)
sys.modules["homeassistant.components"] = MagicMock()

# Stub voluptuous (used by services.py)
_voluptuous = MagicMock()
_voluptuous.Schema = lambda *args, **kwargs: lambda v: v
_voluptuous.Required = lambda v: v
sys.modules["voluptuous"] = _voluptuous


# ------------------------------------------------------------------ sample data


@pytest.fixture
def sample_hydrotap():
    """Return a sample hydrotap dict (from list endpoint)."""
    return {
        "hydrotapId": "631a3385-301b-4c9c-97ed-3a1a50061f5c",
        "serialNumber": "2017102302086",
        "moduleName": "BC 100/75",
        "firmwareVersion": "B03.1.00 3.6 1.05",
        "calibrationDate": "2017-11-06T00:00:00.000Z",
        "status": "No alerts",
        "filterLifeRemainingLitres": 5984,
        "filterLifeRemainingDays": 350,
        "filterLifeRemainingEstimated": 350,
        "averageDailyUsage": 4.6,
        "peakHourlyUsage": 2.8,
        "lastSyncTimestamp": "2026-07-17T08:35:32+0000",
        "buildingName": "The Warehouse",
        "level": "1",
        "locationInBuilding": "Kitchen",
        "country": "Australia",
        "state": "New South Wales",
        "zipManaged": False,
        "connectionKey": None,
        "ownerCompanyName": "Test Corp",
        "facilityManagerCompanyName": None,
        "permissions": {"view": True, "edit": True},
        "hydrotapGroups": [],
        "groupName": None,
        "retired": None,
    }


@pytest.fixture
def sample_hydrotap_no_location():
    """Return a hydrotap with no location fields."""
    return {
        "hydrotapId": "abc-123",
        "serialNumber": "12345",
        "moduleName": "AI 200",
        "firmwareVersion": "1.0",
        "status": "OK",
        "filterLifeRemainingLitres": 1000,
        "filterLifeRemainingDays": 100,
        "filterLifeRemainingEstimated": 100,
        "averageDailyUsage": 2.0,
        "peakHourlyUsage": 1.0,
        "lastSyncTimestamp": "2026-01-01T00:00:00+0000",
    }


@pytest.fixture
def sample_settings():
    """Return sample settings for a hydrotap."""
    return {
        "hydrotapId": "631a3385-301b-4c9c-97ed-3a1a50061f5c",
        "syncPeriod": "00:10:00",
        "sleepModeCode": 6,
        "safetyLockEnabled": True,
        "allowSafetySettingChange": True,
        "hotIsolationEnabled": False,
        "zipManaged": False,
        "language": "en",
        "externalFilterLimits": {"days": None, "litres": None},
        "internalFilterLimits": {"days": 360, "litres": 6000},
        "boiling": {"temp": 98, "duration": 15, "isFeature": True},
        "chilled": {"temp": 5, "duration": 15, "isFeature": True},
        "sparkling": {"temp": None, "duration": 15, "isFeature": False},
        "ambient": {"duration": 15, "isFeature": False},
        "security": {
            "pin": {"enabled": False, "value": None},
            "hydrotapCanModify": True,
        },
        "energy": {
            "activeMode": "everyday",
            "everyday": {
                "onTimeActive": False,
                "onTime": "07:00:00",
                "offTimeActive": True,
                "offTime": "19:00:00",
            },
        },
    }


@pytest.fixture
def sample_settings_options():
    """Return sample settings-options for a hydrotap."""
    return {
        "water": {
            "ambient": False,
            "boiling": {
                "temp": {"min": 68, "max": 100, "step": 0.5},
                "duration": {"min": 5, "max": 15, "step": 1},
            },
            "chilled": {
                "temp": {"min": 5, "max": 9, "step": 1, "range": 4},
                "duration": {"min": 5, "max": 15, "step": 1},
            },
            "sparkling": False,
        },
        "filters": {
            "internal": {
                "litres": {"default": 6000, "min": 500, "max": 10000, "step": 500},
                "days": {"default": 360, "min": 30, "max": 420, "step": 30},
            },
            "external": {
                "litres": {"default": 6000, "min": 500, "max": 10000, "step": 500},
                "days": {"default": 360, "min": 30, "max": 420, "step": 30},
            },
        },
        "safety": {
            "safetyLockEnabled": True,
            "hotIsolationEnabled": True,
            "allowSafetySettingChange": True,
        },
        "syncPeriod": {"min": "00:10:00", "max": "01:00:00", "step": "00:10:00"},
    }


@pytest.fixture
def sample_faults():
    """Return sample current faults."""
    return [
        {
            "hydrotapSystemFaultId": "fault-1",
            "faultCode": "F01",
            "description": "Water leak detected",
            "startTimestamp": "2026-07-17T08:00:00+0000",
            "endTimestamp": None,
        },
    ]


@pytest.fixture
def sample_faults_empty():
    """Return empty faults list."""
    return []


# ------------------------------------------------------------------ mocks


@pytest.fixture
def mock_client():
    """Return a mock ZipAssistClient."""
    client = MagicMock()
    client.authenticate = AsyncMock(return_value=True)
    client.close = AsyncMock()
    client.get_hydrotaps = AsyncMock()
    client.get_settings = AsyncMock()
    client.get_settings_options = AsyncMock()
    client.get_current_faults = AsyncMock()
    client.update_settings = AsyncMock(return_value=True)
    client.clear_fault = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_coordinator(mock_client, sample_hydrotap, sample_settings, sample_settings_options, sample_faults):
    """Return a mock DataUpdateCoordinator with sample data."""
    coordinator = MagicMock()
    coordinator.client = mock_client
    coordinator.data = {
        "hydrotaps": [sample_hydrotap],
        "settings": {sample_hydrotap["hydrotapId"]: sample_settings},
        "settings_options": {sample_hydrotap["hydrotapId"]: sample_settings_options},
        "faults": {sample_hydrotap["hydrotapId"]: sample_faults},
    }
    coordinator.async_request_refresh = AsyncMock()
    return coordinator