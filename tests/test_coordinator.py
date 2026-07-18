"""Tests for the ZipAssist coordinator."""

from __future__ import annotations

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "custom_components"),
)

from zipassist.coordinator import ZipAssistCoordinator  # noqa: E402


class TestCoordinator:
    """Tests for the DataUpdateCoordinator."""

    @pytest.mark.asyncio
    async def test_async_update_data(self, mock_client, sample_hydrotap) -> None:
        """Test coordinator fetches all data on update."""
        mock_client.get_hydrotaps = AsyncMock(return_value=[sample_hydrotap])
        mock_client.get_settings = AsyncMock(
            return_value={"safetyLockEnabled": True}
        )
        mock_client.get_settings_options = AsyncMock(
            return_value={"safety": {"safetyLockEnabled": True}}
        )
        mock_client.get_current_faults = AsyncMock(
            return_value=[{"faultCode": "F01"}]
        )

        hass = MagicMock()
        coordinator = ZipAssistCoordinator(hass, mock_client)

        data = await coordinator._async_update_data()

        assert "hydrotaps" in data
        assert len(data["hydrotaps"]) == 1
        assert "settings" in data
        assert sample_hydrotap["hydrotapId"] in data["settings"]
        assert "settings_options" in data
        assert "faults" in data
        assert len(data["faults"][sample_hydrotap["hydrotapId"]]) == 1

    @pytest.mark.asyncio
    async def test_async_update_data_settings_failure(
        self, mock_client, sample_hydrotap
    ) -> None:
        """Test coordinator handles settings fetch failure gracefully."""
        mock_client.get_hydrotaps = AsyncMock(return_value=[sample_hydrotap])
        mock_client.get_settings = AsyncMock(
            side_effect=Exception("Network error")
        )
        mock_client.get_settings_options = AsyncMock(return_value={})
        mock_client.get_current_faults = AsyncMock(return_value=[])

        hass = MagicMock()
        coordinator = ZipAssistCoordinator(hass, mock_client)

        data = await coordinator._async_update_data()

        # Should still return hydrotaps even if settings fail
        assert len(data["hydrotaps"]) == 1
        assert sample_hydrotap["hydrotapId"] not in data["settings"]

    @pytest.mark.asyncio
    async def test_async_update_data_no_hydrotaps(self, mock_client) -> None:
        """Test coordinator handles empty hydrotap list."""
        mock_client.get_hydrotaps = AsyncMock(return_value=[])

        hass = MagicMock()
        coordinator = ZipAssistCoordinator(hass, mock_client)

        data = await coordinator._async_update_data()

        assert data["hydrotaps"] == []
        assert data["settings"] == {}
        assert data["settings_options"] == {}
        assert data["faults"] == {}

    @pytest.mark.asyncio
    async def test_async_update_data_no_hydrotap_id(
        self, mock_client
    ) -> None:
        """Test coordinator skips hydrotaps with no ID."""
        mock_client.get_hydrotaps = AsyncMock(
            return_value=[{"moduleName": "No ID"}]
        )

        hass = MagicMock()
        coordinator = ZipAssistCoordinator(hass, mock_client)

        data = await coordinator._async_update_data()

        assert len(data["hydrotaps"]) == 1
        assert data["settings"] == {}
        # client.get_settings should not have been called
        mock_client.get_settings.assert_not_called()