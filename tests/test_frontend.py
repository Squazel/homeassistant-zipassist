"""Tests for frontend card registration helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import custom_components.zipassist as zipassist_init
from custom_components.zipassist import (
    DATA_FRONTEND_REGISTERED,
    _async_register_frontend_card,
    _integration_version,
)
from custom_components.zipassist.const import DOMAIN


def test_integration_version_reads_manifest() -> None:
    """Version helper returns the manifest version string."""
    version = _integration_version()
    assert version == "0.1.4"


@pytest.mark.asyncio
async def test_register_frontend_card_idempotent() -> None:
    """Frontend setup runs once only."""
    hass = MagicMock()
    hass.data = {DOMAIN: {}}
    hass.async_add_executor_job = AsyncMock(side_effect=lambda fn: fn())

    setup_fe = AsyncMock()

    with patch.object(zipassist_init, "async_setup_frontend", setup_fe):
        await _async_register_frontend_card(hass)
        await _async_register_frontend_card(hass)

    assert hass.data[DOMAIN][DATA_FRONTEND_REGISTERED] is True
    setup_fe.assert_awaited_once()
    assert setup_fe.await_args.args[1] == "0.1.4"


@pytest.mark.asyncio
async def test_async_setup_frontend_registers_static_path() -> None:
    """Card static path is registered under /zipassist."""
    from custom_components.zipassist import frontend_register as fr

    hass = MagicMock()
    hass.data = {}
    register = AsyncMock()

    with patch.object(fr, "async_register_static_path", register), patch.object(
        fr, "async_init_lovelace_resource", AsyncMock()
    ) as init_res:
        await fr.async_setup_frontend(hass, "0.1.4")

    register.assert_awaited_once()
    assert register.await_args.args[1] == "/zipassist"
    init_res.assert_awaited_once()
    assert init_res.await_args.args[1] == "/zipassist/zipassist-card.js"
    assert init_res.await_args.args[2] == "0.1.4"


def test_card_js_exists_and_defines_element() -> None:
    """Ship a card file that registers the custom element."""
    card = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "zipassist"
        / "frontend"
        / "zipassist-card.js"
    )
    text = card.read_text(encoding="utf-8")
    assert "customElements.define" in text
    assert "zipassist-card" in text
    assert "ha-card" in text
    assert "attachShadow" in text
    assert "getConfigForm" in text
    assert "getStubConfig" in text
    assert "documentationURL" in text
    assert "preview: false" in text
    assert "must be sync and never throw" in text
    assert "&" + "amp;" in text
    assert "&" + "lt;" in text
    assert "&" + "gt;" in text
