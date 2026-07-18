"""Tests for the ZipAssist config flow."""

from __future__ import annotations

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Make the zipassist package importable
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "custom_components"),
)

from zipassist.config_flow import ZipAssistConfigFlow  # noqa: E402


class TestConfigFlow:
    """Tests for config flow."""

    def test_config_flow_init(self) -> None:
        """Test config flow initializes."""
        flow = ZipAssistConfigFlow()
        assert flow.domain == "zipassist"
        assert flow.VERSION == 1

    @pytest.mark.asyncio
    async def test_step_user_auth_success(self) -> None:
        """Test successful authentication during config flow."""
        flow = ZipAssistConfigFlow()
        # Mock the async_set_unique_id and _abort_if_unique_id_configured
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        flow.async_create_entry = MagicMock()

        with patch(
            "zipassist.config_flow.ZipAssistClient",
            autospec=True,
        ) as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.authenticate = AsyncMock(return_value=True)
            mock_client.close = AsyncMock()

            await flow.async_step_user(
                {
                    "email": "test@example.com",
                    "password": "secret",
                    "base_url": "https://zipassist.zipindustries.com",
                }
            )

        flow.async_set_unique_id.assert_called_once_with("zipassist_test@example.com")
        flow.async_create_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_step_user_invalid_auth(self) -> None:
        """Test invalid auth during config flow."""
        flow = ZipAssistConfigFlow()
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        flow.async_show_form = MagicMock()
        flow.async_create_entry = MagicMock()

        with patch(
            "zipassist.config_flow.ZipAssistClient",
            autospec=True,
        ) as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.authenticate = AsyncMock(return_value=False)
            mock_client.close = AsyncMock()

            await flow.async_step_user(
                {
                    "email": "test@example.com",
                    "password": "wrong",
                }
            )

        # Should show form with error
        flow.async_show_form.assert_called()
        call_kwargs = flow.async_show_form.call_args.kwargs
        assert call_kwargs["errors"]["base"] == "invalid_auth"
        flow.async_create_entry.assert_not_called()

    @pytest.mark.asyncio
    async def test_step_user_connection_error(self) -> None:
        """Test connection error during config flow."""
        flow = ZipAssistConfigFlow()
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        flow.async_show_form = MagicMock()
        flow.async_create_entry = MagicMock()

        with patch(
            "zipassist.config_flow.ZipAssistClient",
            autospec=True,
        ) as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.authenticate = AsyncMock(
                side_effect=Exception("Connection refused")
            )
            mock_client.close = AsyncMock()

            await flow.async_step_user(
                {
                    "email": "test@example.com",
                    "password": "secret",
                }
            )

        flow.async_show_form.assert_called()
        call_kwargs = flow.async_show_form.call_args.kwargs
        assert call_kwargs["errors"]["base"] == "cannot_connect"
        flow.async_create_entry.assert_not_called()

    @pytest.mark.asyncio
    async def test_step_user_no_input(self) -> None:
        """Test showing the form with no input."""
        flow = ZipAssistConfigFlow()
        flow.async_show_form = MagicMock()

        await flow.async_step_user(None)

        flow.async_show_form.assert_called_once()
        call_kwargs = flow.async_show_form.call_args.kwargs
        assert call_kwargs["step_id"] == "user"
        assert call_kwargs["errors"] == {}