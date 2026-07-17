"""Tests for entity creation and state logic."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

import pytest

# Make the zipassist package importable
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "custom_components"),
)

from zipassist.sensor import (  # noqa: E402
    SENSOR_TYPES,
    ZipAssistSensor,
)
from zipassist.number import (  # noqa: E402
    NUMBER_TYPES,
    ZipAssistNumber,
)
from zipassist.binary_sensor import (  # noqa: E402
    BINARY_SENSOR_TYPES,
    ZipAssistBinarySensor,
)
from zipassist.switch import (  # noqa: E402
    SWITCH_TYPES,
    ZipAssistSwitch,
)
from zipassist.select import (  # noqa: E402
    SELECT_TYPES,
    ZipAssistSelect,
)


# ------------------------------------------------------------------ sensor entities


class TestSensorEntities:
    """Tests for sensor entity creation and state."""

    def test_all_sensor_types_defined(self) -> None:
        """Test all expected sensor types are defined."""
        keys = {d.key for d in SENSOR_TYPES}
        expected = {
            "filter_litres_remaining",
            "filter_days_remaining",
            "filter_estimated_days",
            "average_daily_usage",
            "peak_hourly_usage",
            "last_sync",
            "status",
            "serial_number",
            "firmware_version",
            "system_fault_details",
        }
        assert keys == expected

    def test_sensor_creation(self, mock_coordinator, sample_hydrotap) -> None:
        """Test creating a sensor entity."""
        desc = SENSOR_TYPES[0]  # filter_litres_remaining
        entity = ZipAssistSensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.unique_id == "631a3385-301b-4c9c-97ed-3a1a50061f5c_filter_litres_remaining"
        assert entity.device_info is not None
        assert entity.device_info["manufacturer"] == "Zip Industries"
        assert entity.device_info["model"] == "BC 100/75"

    def test_sensor_native_value(self, mock_coordinator, sample_hydrotap) -> None:
        """Test sensor returns correct native value."""
        desc = SENSOR_TYPES[0]  # filter_litres_remaining
        entity = ZipAssistSensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == 5984

    def test_sensor_status(self, mock_coordinator, sample_hydrotap) -> None:
        """Test status sensor."""
        desc = SENSOR_TYPES[6]  # status
        entity = ZipAssistSensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == "No alerts"

    def test_sensor_last_sync(self, mock_coordinator, sample_hydrotap) -> None:
        """Test last_sync sensor."""
        desc = SENSOR_TYPES[5]  # last_sync
        entity = ZipAssistSensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == "2026-07-17T08:35:32+0000"

    def test_sensor_fault_details_with_faults(
        self, mock_coordinator, sample_hydrotap
    ) -> None:
        """Test fault details sensor with active faults."""
        desc = SENSOR_TYPES[9]  # system_fault_details
        entity = ZipAssistSensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == "F01"

    def test_sensor_fault_details_no_faults(
        self, mock_coordinator, sample_hydrotap
    ) -> None:
        """Test fault details sensor with no faults."""
        mock_coordinator.data["faults"] = {}
        desc = SENSOR_TYPES[9]  # system_fault_details
        entity = ZipAssistSensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == "No faults"

    def test_sensor_fault_details_multiple_faults(
        self, mock_coordinator, sample_hydrotap
    ) -> None:
        """Test fault details sensor with multiple faults."""
        mock_coordinator.data["faults"] = {
            sample_hydrotap["hydrotapId"]: [
                {"faultCode": "F01", "description": "Leak"},
                {"faultCode": "F02", "description": "Filter"},
            ]
        }
        desc = SENSOR_TYPES[9]  # system_fault_details
        entity = ZipAssistSensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == "F01, F02"

    def test_sensor_hydrotap_not_found(self, mock_coordinator) -> None:
        """Test sensor returns None when hydrotap not in data."""
        hydrotap = {"hydrotapId": "nonexistent", "moduleName": "X"}
        desc = SENSOR_TYPES[0]
        entity = ZipAssistSensor(mock_coordinator, hydrotap, desc)
        assert entity.native_value is None


# ------------------------------------------------------------------ number entities


class TestNumberEntities:
    """Tests for number entity creation and state."""

    def test_all_number_types_defined(self) -> None:
        """Test all expected number types are defined."""
        keys = {d.key for d in NUMBER_TYPES}
        expected = {
            "boiling_temp",
            "chilled_temp",
            "boiling_duration",
            "chilled_duration",
            "sparkling_duration",
            "ambient_duration",
            "internal_filter_litres",
            "internal_filter_days",
            "external_filter_litres",
            "external_filter_days",
        }
        assert keys == expected

    def test_number_creation(self, mock_coordinator, sample_hydrotap) -> None:
        """Test creating a number entity."""
        desc = NUMBER_TYPES[0]  # boiling_temp
        entity = ZipAssistNumber(mock_coordinator, sample_hydrotap, desc)
        assert entity.unique_id == "631a3385-301b-4c9c-97ed-3a1a50061f5c_boiling_temp"
        assert entity.entity_description.native_unit_of_measurement == "°C"

    def test_number_native_value(self, mock_coordinator, sample_hydrotap) -> None:
        """Test number returns correct value."""
        desc = NUMBER_TYPES[0]  # boiling_temp
        entity = ZipAssistNumber(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == 98

    def test_number_chilled_temp(self, mock_coordinator, sample_hydrotap) -> None:
        """Test chilled temp number."""
        desc = NUMBER_TYPES[1]  # chilled_temp
        entity = ZipAssistNumber(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == 5

    def test_number_range_from_options(self, mock_coordinator, sample_hydrotap) -> None:
        """Test number range is set from settings-options."""
        desc = NUMBER_TYPES[0]  # boiling_temp
        entity = ZipAssistNumber(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_min_value == 68
        assert entity.native_max_value == 100
        assert entity.native_step == 0.5

    @pytest.mark.asyncio
    async def test_number_set_value(self, mock_coordinator, sample_hydrotap) -> None:
        """Test setting a number value."""
        desc = NUMBER_TYPES[0]  # boiling_temp
        entity = ZipAssistNumber(mock_coordinator, sample_hydrotap, desc)
        await entity.async_set_native_value(95.0)
        mock_coordinator.client.update_settings.assert_called_once_with(
            "631a3385-301b-4c9c-97ed-3a1a50061f5c",
            {"boiling": {"temp": 95.0}},
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_number_set_value_failure(
        self, mock_coordinator, sample_hydrotap
    ) -> None:
        """Test setting a number value when API fails."""
        mock_coordinator.client.update_settings.return_value = False
        desc = NUMBER_TYPES[0]
        entity = ZipAssistNumber(mock_coordinator, sample_hydrotap, desc)
        await entity.async_set_native_value(95.0)
        mock_coordinator.async_request_refresh.assert_not_called()

    # --- dispense duration ---

    def test_boiling_duration_value(self, mock_coordinator, sample_hydrotap) -> None:
        """Test boiling duration number."""
        desc = NUMBER_TYPES[2]  # boiling_duration
        entity = ZipAssistNumber(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == 15
        assert entity.entity_description.native_unit_of_measurement == "s"

    def test_sparkling_duration_not_available(self) -> None:
        """Test sparkling duration is not available when isFeature=False."""
        desc = NUMBER_TYPES[4]  # sparkling_duration
        settings = {"sparkling": {"duration": 15, "isFeature": False}}
        assert desc.available_fn(settings) is False

    # --- filter limits ---

    def test_internal_filter_litres_value(
        self, mock_coordinator, sample_hydrotap
    ) -> None:
        """Test internal filter litres number."""
        desc = NUMBER_TYPES[6]  # internal_filter_litres
        entity = ZipAssistNumber(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == 6000

    def test_internal_filter_days_value(
        self, mock_coordinator, sample_hydrotap
    ) -> None:
        """Test internal filter days number."""
        desc = NUMBER_TYPES[7]  # internal_filter_days
        entity = ZipAssistNumber(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == 360

    def test_external_filter_not_available(self) -> None:
        """Test external filter is not available when value is None."""
        desc = NUMBER_TYPES[8]  # external_filter_litres
        settings = {"externalFilterLimits": {"days": None, "litres": None}}
        assert desc.available_fn(settings) is False

    def test_filter_range_from_options(
        self, mock_coordinator, sample_hydrotap
    ) -> None:
        """Test filter limit range is set from settings-options."""
        desc = NUMBER_TYPES[6]  # internal_filter_litres
        entity = ZipAssistNumber(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_min_value == 500
        assert entity.native_max_value == 10000
        assert entity.native_step == 500

    @pytest.mark.asyncio
    async def test_filter_set_value(self, mock_coordinator, sample_hydrotap) -> None:
        """Test setting a filter limit value."""
        desc = NUMBER_TYPES[6]  # internal_filter_litres
        entity = ZipAssistNumber(mock_coordinator, sample_hydrotap, desc)
        await entity.async_set_native_value(5000.0)
        mock_coordinator.client.update_settings.assert_called_once_with(
            "631a3385-301b-4c9c-97ed-3a1a50061f5c",
            {"internalFilterLimits": {"litres": 5000.0}},
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_duration_set_value(self, mock_coordinator, sample_hydrotap) -> None:
        """Test setting a dispense duration value."""
        desc = NUMBER_TYPES[2]  # boiling_duration
        entity = ZipAssistNumber(mock_coordinator, sample_hydrotap, desc)
        await entity.async_set_native_value(10.0)
        mock_coordinator.client.update_settings.assert_called_once_with(
            "631a3385-301b-4c9c-97ed-3a1a50061f5c",
            {"boiling": {"duration": 10.0}},
        )
        mock_coordinator.async_request_refresh.assert_called_once()


# ------------------------------------------------------------------ binary sensor entities


class TestBinarySensorEntities:
    """Tests for binary sensor entity creation and state."""

    def test_all_binary_sensor_types_defined(self) -> None:
        """Test all expected binary sensor types are defined."""
        keys = {d.key for d in BINARY_SENSOR_TYPES}
        assert keys == {"safety_lock", "hot_isolation", "system_fault"}

    def test_binary_sensor_creation(self, mock_coordinator, sample_hydrotap) -> None:
        """Test creating a binary sensor entity."""
        desc = BINARY_SENSOR_TYPES[0]  # safety_lock
        entity = ZipAssistBinarySensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.unique_id == "631a3385-301b-4c9c-97ed-3a1a50061f5c_safety_lock"

    def test_safety_lock_on(self, mock_coordinator, sample_hydrotap) -> None:
        """Test safety lock is_on."""
        desc = BINARY_SENSOR_TYPES[0]  # safety_lock
        entity = ZipAssistBinarySensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.is_on is True

    def test_hot_isolation_off(self, mock_coordinator, sample_hydrotap) -> None:
        """Test hot isolation is_on when disabled."""
        desc = BINARY_SENSOR_TYPES[1]  # hot_isolation
        entity = ZipAssistBinarySensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.is_on is False

    def test_system_fault_on(self, mock_coordinator, sample_hydrotap) -> None:
        """Test system_fault is_on when faults exist."""
        desc = BINARY_SENSOR_TYPES[2]  # system_fault
        entity = ZipAssistBinarySensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.is_on is True

    def test_system_fault_off(self, mock_coordinator, sample_hydrotap) -> None:
        """Test system_fault is_on when no faults."""
        mock_coordinator.data["faults"] = {
            sample_hydrotap["hydrotapId"]: []
        }
        desc = BINARY_SENSOR_TYPES[2]  # system_fault
        entity = ZipAssistBinarySensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.is_on is False

    def test_system_fault_device_class(self) -> None:
        """Test system_fault has PROBLEM device class."""
        desc = BINARY_SENSOR_TYPES[2]
        assert desc.device_class is not None
        # BinarySensorDeviceClass.PROBLEM = "problem"
        assert desc.device_class.value == "problem"


# ------------------------------------------------------------------ switch entities


class TestSwitchEntities:
    """Tests for switch entity creation and state."""

    def test_all_switch_types_defined(self) -> None:
        """Test all expected switch types are defined."""
        keys = {d.key for d in SWITCH_TYPES}
        assert keys == {"safety_lock", "hot_isolation"}

    def test_switch_creation(self, mock_coordinator, sample_hydrotap) -> None:
        """Test creating a switch entity."""
        desc = SWITCH_TYPES[0]  # safety_lock
        entity = ZipAssistSwitch(mock_coordinator, sample_hydrotap, desc)
        assert entity.unique_id == "631a3385-301b-4c9c-97ed-3a1a50061f5c_safety_lock"
        assert entity.device_info is not None

    def test_switch_is_on(self, mock_coordinator, sample_hydrotap) -> None:
        """Test switch is_on."""
        desc = SWITCH_TYPES[0]  # safety_lock
        entity = ZipAssistSwitch(mock_coordinator, sample_hydrotap, desc)
        assert entity.is_on is True

    def test_switch_is_off(self, mock_coordinator, sample_hydrotap) -> None:
        """Test switch is_on when disabled."""
        desc = SWITCH_TYPES[1]  # hot_isolation
        entity = ZipAssistSwitch(mock_coordinator, sample_hydrotap, desc)
        assert entity.is_on is False

    @pytest.mark.asyncio
    async def test_switch_turn_on(self, mock_coordinator, sample_hydrotap) -> None:
        """Test turning a switch on."""
        desc = SWITCH_TYPES[0]  # safety_lock
        entity = ZipAssistSwitch(mock_coordinator, sample_hydrotap, desc)
        await entity.async_turn_on()
        mock_coordinator.client.update_settings.assert_called_once_with(
            "631a3385-301b-4c9c-97ed-3a1a50061f5c",
            {"safetyLockEnabled": True},
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_switch_turn_off(self, mock_coordinator, sample_hydrotap) -> None:
        """Test turning a switch off."""
        desc = SWITCH_TYPES[1]  # hot_isolation
        entity = ZipAssistSwitch(mock_coordinator, sample_hydrotap, desc)
        await entity.async_turn_off()
        mock_coordinator.client.update_settings.assert_called_once_with(
            "631a3385-301b-4c9c-97ed-3a1a50061f5c",
            {"hotIsolationEnabled": False},
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_switch_turn_on_failure(
        self, mock_coordinator, sample_hydrotap
    ) -> None:
        """Test turning a switch on when API fails."""
        mock_coordinator.client.update_settings.return_value = False
        desc = SWITCH_TYPES[0]
        entity = ZipAssistSwitch(mock_coordinator, sample_hydrotap, desc)
        await entity.async_turn_on()
        mock_coordinator.async_request_refresh.assert_not_called()

    def test_switch_available_fn(self) -> None:
        """Test available_fn for switch types."""
        # safety_lock available when settings-options says so
        opts = {"safety": {"safetyLockEnabled": True, "hotIsolationEnabled": False}}
        assert SWITCH_TYPES[0].available_fn(opts) is True
        assert SWITCH_TYPES[1].available_fn(opts) is False

    def test_switch_setting_key(self) -> None:
        """Test setting_key for switch types."""
        assert SWITCH_TYPES[0].setting_key == "safetyLockEnabled"
        assert SWITCH_TYPES[1].setting_key == "hotIsolationEnabled"


# ------------------------------------------------------------------ select entities


class TestSelectEntities:
    """Tests for select entity creation and state."""

    def test_all_select_types_defined(self) -> None:
        """Test all expected select types are defined."""
        keys = {d.key for d in SELECT_TYPES}
        assert keys == {"sleep_mode", "energy_mode"}

    def test_select_creation(self, mock_coordinator, sample_hydrotap) -> None:
        """Test creating a select entity."""
        desc = SELECT_TYPES[0]  # sleep_mode
        entity = ZipAssistSelect(mock_coordinator, sample_hydrotap, desc)
        assert entity.unique_id == "631a3385-301b-4c9c-97ed-3a1a50061f5c_sleep_mode"
        assert entity.device_info is not None

    def test_sleep_mode_current_option(self, mock_coordinator, sample_hydrotap) -> None:
        """Test sleep mode current option."""
        desc = SELECT_TYPES[0]  # sleep_mode
        entity = ZipAssistSelect(mock_coordinator, sample_hydrotap, desc)
        assert entity.current_option == "6"

    def test_energy_mode_current_option(self, mock_coordinator, sample_hydrotap) -> None:
        """Test energy mode current option."""
        desc = SELECT_TYPES[1]  # energy_mode
        entity = ZipAssistSelect(mock_coordinator, sample_hydrotap, desc)
        assert entity.current_option == "everyday"

    def test_select_options(self, mock_coordinator, sample_hydrotap) -> None:
        """Test select entity has correct options."""
        desc = SELECT_TYPES[0]  # sleep_mode
        entity = ZipAssistSelect(mock_coordinator, sample_hydrotap, desc)
        assert "0" in entity.options
        assert "8" in entity.options
        assert len(entity.options) == 9

    def test_energy_mode_options(self, mock_coordinator, sample_hydrotap) -> None:
        """Test energy mode has correct options."""
        desc = SELECT_TYPES[1]  # energy_mode
        entity = ZipAssistSelect(mock_coordinator, sample_hydrotap, desc)
        assert entity.options == ["everyday", "daily", "weekdayWeekend"]

    @pytest.mark.asyncio
    async def test_select_option_sleep(self, mock_coordinator, sample_hydrotap) -> None:
        """Test selecting a sleep mode option."""
        desc = SELECT_TYPES[0]  # sleep_mode
        entity = ZipAssistSelect(mock_coordinator, sample_hydrotap, desc)
        await entity.async_select_option("3")
        mock_coordinator.client.update_settings.assert_called_once_with(
            "631a3385-301b-4c9c-97ed-3a1a50061f5c",
            {"sleepModeCode": 3},
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_select_option_energy(self, mock_coordinator, sample_hydrotap) -> None:
        """Test selecting an energy mode option."""
        desc = SELECT_TYPES[1]  # energy_mode
        entity = ZipAssistSelect(mock_coordinator, sample_hydrotap, desc)
        await entity.async_select_option("daily")
        mock_coordinator.client.update_settings.assert_called_once_with(
            "631a3385-301b-4c9c-97ed-3a1a50061f5c",
            {"energy": {"activeMode": "daily"}},
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_select_option_failure(
        self, mock_coordinator, sample_hydrotap
    ) -> None:
        """Test selecting an option when API fails."""
        mock_coordinator.client.update_settings.return_value = False
        desc = SELECT_TYPES[0]
        entity = ZipAssistSelect(mock_coordinator, sample_hydrotap, desc)
        await entity.async_select_option("3")
        mock_coordinator.async_request_refresh.assert_not_called()