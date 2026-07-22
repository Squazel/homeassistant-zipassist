"""Tests for entity creation and state logic."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

import pytest

# Make the zipassist package importable
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "custom_components"),
)

from homeassistant.components.sensor import SensorDeviceClass  # noqa: E402

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
from zipassist.time import (  # noqa: E402
    TIME_TYPES,
    ZipAssistTime,
    _parse_time,
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
            "wifi_signal_strength",
            "energy_since_last_log",
            "energy_total",
            "sleep_mode_status",
            "litres_filtered_internal",
            "litres_filtered_external",
            "days_filtered_internal",
            "days_filtered_external",
        }
        assert keys == expected

    def test_sensor_creation(self, mock_coordinator, sample_hydrotap) -> None:
        """Test creating a sensor entity."""
        desc = SENSOR_TYPES[0]  # filter_litres_remaining
        entity = ZipAssistSensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.unique_id == "zipassist_00000000-0000-0000-0000-000000000001_filter_litres_remaining"
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
        """Test last_sync sensor returns datetime for TIMESTAMP device class."""
        desc = SENSOR_TYPES[5]  # last_sync
        entity = ZipAssistSensor(mock_coordinator, sample_hydrotap, desc)
        expected = datetime(2026, 7, 17, 8, 35, 32, tzinfo=timezone.utc)
        assert entity.native_value == expected
        assert desc.device_class == SensorDeviceClass.TIMESTAMP

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

    def test_sensor_available(self, mock_coordinator, sample_hydrotap) -> None:
        """Test sensor available property."""
        desc = SENSOR_TYPES[0]
        entity = ZipAssistSensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.available is True

    def test_sensor_unavailable(self, mock_coordinator, sample_hydrotap) -> None:
        """Test sensor unavailable when coordinator fails."""
        mock_coordinator.last_update_success = False
        desc = SENSOR_TYPES[0]
        entity = ZipAssistSensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.available is False

    # --- status log sensors ---

    def test_wifi_signal_strength(self, mock_coordinator, sample_hydrotap) -> None:
        """Test wifi signal strength sensor."""
        desc = SENSOR_TYPES[10]  # wifi_signal_strength
        entity = ZipAssistSensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == -55

    def test_energy_since_last_log(self, mock_coordinator, sample_hydrotap) -> None:
        """Test energy since last log sensor."""
        desc = SENSOR_TYPES[11]  # energy_since_last_log
        entity = ZipAssistSensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == 0.5

    def test_energy_total(self, mock_coordinator, sample_hydrotap) -> None:
        """Test total energy sensor."""
        desc = SENSOR_TYPES[12]  # energy_total
        entity = ZipAssistSensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == 1234.5

    def test_sleep_mode_status(self, mock_coordinator, sample_hydrotap) -> None:
        """Test sleep mode status sensor."""
        desc = SENSOR_TYPES[13]  # sleep_mode_status
        entity = ZipAssistSensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == "active"

    def test_litres_filtered_internal(self, mock_coordinator, sample_hydrotap) -> None:
        """Test internal litres filtered sensor."""
        desc = SENSOR_TYPES[14]  # litres_filtered_internal
        entity = ZipAssistSensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == 200

    def test_days_filtered_internal(self, mock_coordinator, sample_hydrotap) -> None:
        """Test internal days filtered sensor."""
        desc = SENSOR_TYPES[16]  # days_filtered_internal
        entity = ZipAssistSensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == 15

    def test_diagnostic_category(self) -> None:
        """Test diagnostic sensors have DIAGNOSTIC entity category."""
        diagnostic_keys = {
            "last_sync",
            "status", "serial_number", "firmware_version",
            "system_fault_details", "wifi_signal_strength", "energy_since_last_log",
            "energy_total", "sleep_mode_status", "litres_filtered_internal",
            "litres_filtered_external", "days_filtered_internal", "days_filtered_external",
        }
        for desc in SENSOR_TYPES:
            if desc.key in diagnostic_keys:
                assert desc.entity_category == "diagnostic", f"{desc.key} should be DIAGNOSTIC"
            else:
                assert desc.entity_category is None, f"{desc.key} should not be DIAGNOSTIC"


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
        assert entity.unique_id == "zipassist_00000000-0000-0000-0000-000000000001_boiling_temp"
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
            "00000000-0000-0000-0000-000000000001",
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
            "00000000-0000-0000-0000-000000000001",
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
            "00000000-0000-0000-0000-000000000001",
            {"boiling": {"duration": 10.0}},
        )
        mock_coordinator.async_request_refresh.assert_called_once()


    def test_number_available(self, mock_coordinator, sample_hydrotap) -> None:
        """Test number available property."""
        desc = NUMBER_TYPES[0]
        entity = ZipAssistNumber(mock_coordinator, sample_hydrotap, desc)
        assert entity.available is True

    def test_number_unavailable(self, mock_coordinator, sample_hydrotap) -> None:
        """Test number unavailable when coordinator fails."""
        mock_coordinator.last_update_success = False
        desc = NUMBER_TYPES[0]
        entity = ZipAssistNumber(mock_coordinator, sample_hydrotap, desc)
        assert entity.available is False


# ------------------------------------------------------------------ binary sensor entities


class TestBinarySensorEntities:
    """Tests for binary sensor entity creation and state."""

    def test_all_binary_sensor_types_defined(self) -> None:
        """Test all expected binary sensor types are defined."""
        keys = {d.key for d in BINARY_SENSOR_TYPES}
        assert keys == {"system_fault"}

    def test_binary_sensor_creation(self, mock_coordinator, sample_hydrotap) -> None:
        """Test creating a binary sensor entity."""
        desc = BINARY_SENSOR_TYPES[0]  # system_fault
        entity = ZipAssistBinarySensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.unique_id == "zipassist_00000000-0000-0000-0000-000000000001_system_fault"

    def test_system_fault_on(self, mock_coordinator, sample_hydrotap) -> None:
        """Test system_fault is_on when faults exist."""
        desc = BINARY_SENSOR_TYPES[0]  # system_fault
        entity = ZipAssistBinarySensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.is_on is True

    def test_system_fault_off(self, mock_coordinator, sample_hydrotap) -> None:
        """Test system_fault is_on when no faults."""
        mock_coordinator.data["faults"] = {
            sample_hydrotap["hydrotapId"]: []
        }
        desc = BINARY_SENSOR_TYPES[0]  # system_fault
        entity = ZipAssistBinarySensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.is_on is False

    def test_system_fault_device_class(self) -> None:
        """Test system_fault has PROBLEM device class."""
        desc = BINARY_SENSOR_TYPES[0]
        assert desc.device_class is not None
        # BinarySensorDeviceClass.PROBLEM = "problem"
        assert desc.device_class.value == "problem"

    def test_binary_sensor_available(self, mock_coordinator, sample_hydrotap) -> None:
        """Test binary sensor available property."""
        desc = BINARY_SENSOR_TYPES[0]
        entity = ZipAssistBinarySensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.available is True

    def test_binary_sensor_unavailable(self, mock_coordinator, sample_hydrotap) -> None:
        """Test binary sensor unavailable when coordinator fails."""
        mock_coordinator.last_update_success = False
        desc = BINARY_SENSOR_TYPES[0]
        entity = ZipAssistBinarySensor(mock_coordinator, sample_hydrotap, desc)
        assert entity.available is False


# ------------------------------------------------------------------ switch entities


class TestSwitchEntities:
    """Tests for switch entity creation and state."""

    def test_all_switch_types_defined(self) -> None:
        """Test all expected switch types are defined."""
        keys = {d.key for d in SWITCH_TYPES}
        expected = {
            "safety_lock",
            "hot_isolation",
            "energy_everyday_on_active",
            "energy_everyday_off_active",
            "energy_weekday_on_active",
            "energy_weekday_off_active",
            "energy_weekend_on_active",
            "energy_weekend_off_active",
        }
        for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun"):
            expected.add(f"energy_daily_{day}_on_active")
            expected.add(f"energy_daily_{day}_off_active")
        assert keys == expected

    def test_switch_creation(self, mock_coordinator, sample_hydrotap) -> None:
        """Test creating a switch entity."""
        desc = SWITCH_TYPES[0]  # safety_lock
        entity = ZipAssistSwitch(mock_coordinator, sample_hydrotap, desc)
        assert entity.unique_id == "zipassist_00000000-0000-0000-0000-000000000001_safety_lock"
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
            "00000000-0000-0000-0000-000000000001",
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
            "00000000-0000-0000-0000-000000000001",
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

    def test_energy_everyday_switch(self, mock_coordinator, sample_hydrotap) -> None:
        """Test energy everyday on_active switch."""
        desc = SWITCH_TYPES[2]  # energy_everyday_on_active
        entity = ZipAssistSwitch(mock_coordinator, sample_hydrotap, desc)
        assert entity.is_on is False  # onTimeActive is False in sample

    def test_energy_everyday_off_active(self, mock_coordinator, sample_hydrotap) -> None:
        """Test energy everyday off_active switch."""
        desc = SWITCH_TYPES[3]  # energy_everyday_off_active
        entity = ZipAssistSwitch(mock_coordinator, sample_hydrotap, desc)
        assert entity.is_on is True  # offTimeActive is True in sample

    @pytest.mark.asyncio
    async def test_energy_switch_turn_on(self, mock_coordinator, sample_hydrotap) -> None:
        """Test turning an energy switch on."""
        desc = SWITCH_TYPES[2]  # energy_everyday_on_active
        entity = ZipAssistSwitch(mock_coordinator, sample_hydrotap, desc)
        await entity.async_turn_on()
        mock_coordinator.client.update_settings.assert_called_once_with(
            "00000000-0000-0000-0000-000000000001",
            {"energy": {"everyday": {"onTimeActive": True}}},
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    def test_energy_available_fn(self) -> None:
        """Test energy switch available_fn checks activeMode."""
        settings_everyday = {"energy": {"activeMode": "everyday"}}
        settings_daily = {"energy": {"activeMode": "daily"}}
        # everyday switch available when mode is everyday
        assert SWITCH_TYPES[2].available_fn(settings_everyday) is True
        assert SWITCH_TYPES[2].available_fn(settings_daily) is False

    def test_switch_available(self, mock_coordinator, sample_hydrotap) -> None:
        """Test switch available property."""
        desc = SWITCH_TYPES[0]
        entity = ZipAssistSwitch(mock_coordinator, sample_hydrotap, desc)
        assert entity.available is True

    def test_switch_unavailable(self, mock_coordinator, sample_hydrotap) -> None:
        """Test switch unavailable when coordinator fails."""
        mock_coordinator.last_update_success = False
        desc = SWITCH_TYPES[0]
        entity = ZipAssistSwitch(mock_coordinator, sample_hydrotap, desc)
        assert entity.available is False


# ------------------------------------------------------------------ select entities


class TestSelectEntities:
    """Tests for select entity creation and state."""

    def test_all_select_types_defined(self) -> None:
        """Test all expected select types are defined."""
        keys = {d.key for d in SELECT_TYPES}
        assert keys == {"sleep_mode", "energy_mode", "sync_period"}

    def test_select_creation(self, mock_coordinator, sample_hydrotap) -> None:
        """Test creating a select entity."""
        desc = SELECT_TYPES[0]  # sleep_mode
        entity = ZipAssistSelect(mock_coordinator, sample_hydrotap, desc)
        assert entity.unique_id == "zipassist_00000000-0000-0000-0000-000000000001_sleep_mode"
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
            "00000000-0000-0000-0000-000000000001",
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
            "00000000-0000-0000-0000-000000000001",
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

    def test_sync_period_current_option(
        self, mock_coordinator, sample_hydrotap
    ) -> None:
        """Test sync period current option."""
        desc = SELECT_TYPES[2]  # sync_period
        entity = ZipAssistSelect(mock_coordinator, sample_hydrotap, desc)
        assert entity.current_option == "00:10:00"

    @pytest.mark.asyncio
    async def test_select_option_sync_period(
        self, mock_coordinator, sample_hydrotap
    ) -> None:
        """Test selecting a sync period option."""
        desc = SELECT_TYPES[2]  # sync_period
        entity = ZipAssistSelect(mock_coordinator, sample_hydrotap, desc)
        await entity.async_select_option("00:30:00")
        mock_coordinator.client.update_settings.assert_called_once_with(
            "00000000-0000-0000-0000-000000000001",
            {"syncPeriod": "00:30:00"},
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    def test_select_available(self, mock_coordinator, sample_hydrotap) -> None:
        """Test select available property."""
        desc = SELECT_TYPES[0]
        entity = ZipAssistSelect(mock_coordinator, sample_hydrotap, desc)
        assert entity.available is True

    def test_select_unavailable(self, mock_coordinator, sample_hydrotap) -> None:
        """Test select unavailable when coordinator fails."""
        mock_coordinator.last_update_success = False
        desc = SELECT_TYPES[0]
        entity = ZipAssistSelect(mock_coordinator, sample_hydrotap, desc)
        assert entity.available is False


# ------------------------------------------------------------------ time entities


class TestTimeEntities:
    """Tests for time entity creation and state."""

    def test_all_time_types_defined(self) -> None:
        """Test all expected time types are defined."""
        keys = {d.key for d in TIME_TYPES}
        expected = {
            "energy_everyday_on_time",
            "energy_everyday_off_time",
            "energy_weekday_on_time",
            "energy_weekday_off_time",
            "energy_weekend_on_time",
            "energy_weekend_off_time",
        }
        for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun"):
            expected.add(f"energy_daily_{day}_on_time")
            expected.add(f"energy_daily_{day}_off_time")
        assert keys == expected

    def test_time_creation(self, mock_coordinator, sample_hydrotap) -> None:
        """Test creating a time entity."""
        desc = TIME_TYPES[0]  # energy_everyday_on_time
        entity = ZipAssistTime(mock_coordinator, sample_hydrotap, desc)
        assert entity.unique_id == "zipassist_00000000-0000-0000-0000-000000000001_energy_everyday_on_time"
        assert entity.device_info is not None

    def test_time_native_value(self, mock_coordinator, sample_hydrotap) -> None:
        """Test time returns correct value."""
        from datetime import time as dtime
        desc = TIME_TYPES[0]  # energy_everyday_on_time — "07:00:00"
        entity = ZipAssistTime(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == dtime(7, 0, 0)

    def test_time_off_value(self, mock_coordinator, sample_hydrotap) -> None:
        """Test time off value."""
        from datetime import time as dtime
        desc = TIME_TYPES[1]  # energy_everyday_off_time — "19:00:00"
        entity = ZipAssistTime(mock_coordinator, sample_hydrotap, desc)
        assert entity.native_value == dtime(19, 0, 0)

    @pytest.mark.asyncio
    async def test_time_set_value(self, mock_coordinator, sample_hydrotap) -> None:
        """Test setting a time value."""
        from datetime import time as dtime
        desc = TIME_TYPES[0]  # energy_everyday_on_time
        entity = ZipAssistTime(mock_coordinator, sample_hydrotap, desc)
        await entity.async_set_value(dtime(8, 30, 0))
        mock_coordinator.client.update_settings.assert_called_once_with(
            "00000000-0000-0000-0000-000000000001",
            {"energy": {"everyday": {"onTime": "08:30:00"}}},
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_time_set_value_failure(
        self, mock_coordinator, sample_hydrotap
    ) -> None:
        """Test setting a time value when API fails."""
        from datetime import time as dtime
        mock_coordinator.client.update_settings.return_value = False
        desc = TIME_TYPES[0]
        entity = ZipAssistTime(mock_coordinator, sample_hydrotap, desc)
        await entity.async_set_value(dtime(8, 0, 0))
        mock_coordinator.async_request_refresh.assert_not_called()

    def test_parse_time(self) -> None:
        """Test _parse_time helper."""
        from datetime import time as dtime
        assert _parse_time("07:00:00") == dtime(7, 0, 0)
        assert _parse_time("19:00:00") == dtime(19, 0, 0)
        assert _parse_time("07:00") == dtime(7, 0)
        assert _parse_time(None) is None
        assert _parse_time("") is None
        assert _parse_time("invalid") is None

    def test_time_available(self, mock_coordinator, sample_hydrotap) -> None:
        """Test time available property."""
        desc = TIME_TYPES[0]
        entity = ZipAssistTime(mock_coordinator, sample_hydrotap, desc)
        assert entity.available is True

    def test_time_unavailable(self, mock_coordinator, sample_hydrotap) -> None:
        """Test time unavailable when coordinator fails."""
        mock_coordinator.last_update_success = False
        desc = TIME_TYPES[0]
        entity = ZipAssistTime(mock_coordinator, sample_hydrotap, desc)
        assert entity.available is False