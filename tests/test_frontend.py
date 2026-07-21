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
    assert version == "0.1.0"


@pytest.mark.asyncio
async def test_register_frontend_card_idempotent() -> None:
    """Static path + extra JS are registered once only."""
    hass = MagicMock()
    hass.data = {DOMAIN: {}}
    hass.http.async_register_static_paths = AsyncMock()
    hass.async_add_executor_job = AsyncMock(side_effect=lambda fn: fn())

    add_js = MagicMock()

    # In unit tests HA frontend modules are unavailable, so inject stubs.
    with patch.object(zipassist_init, "FRONTEND_AVAILABLE", True), patch.object(
        zipassist_init, "add_extra_js_url", add_js, create=True
    ), patch.object(
        zipassist_init,
        "StaticPathConfig",
        side_effect=lambda *a, **k: ("static", a, k),
        create=True,
    ):
        await _async_register_frontend_card(hass)
        await _async_register_frontend_card(hass)

    assert hass.data[DOMAIN][DATA_FRONTEND_REGISTERED] is True
    hass.http.async_register_static_paths.assert_awaited_once()
    add_js.assert_called_once()
    url = add_js.call_args.args[1]
    assert url.startswith(f"/{DOMAIN}/zipassist-card.js?v=")
    assert add_js.call_args.kwargs.get("es5") is False


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
    # HTML escaping must encode entities
    assert "&" + "amp;" in text
    assert "&" + "lt;" in text
    assert "&" + "gt;" in text
