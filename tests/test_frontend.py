"""Tests for frontend card registration helpers."""

from __future__ import annotations

import json
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

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MANIFEST_PATH = (
    _REPO_ROOT / "custom_components" / "zipassist" / "manifest.json"
)


def _manifest_version() -> str:
    """Read version from packaged manifest (single source of truth)."""
    data = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    version = data.get("version")
    assert isinstance(version, str) and version.strip()
    return version


def test_integration_version_reads_manifest() -> None:
    """Version helper returns whatever is in manifest.json (no hard-coded pin)."""
    expected = _manifest_version()
    assert _integration_version() == expected


@pytest.mark.asyncio
async def test_register_frontend_card_idempotent() -> None:
    """Frontend setup runs once only and passes the live manifest version."""
    hass = MagicMock()
    hass.data = {DOMAIN: {}}
    hass.async_add_executor_job = AsyncMock(side_effect=lambda fn: fn())

    setup_fe = AsyncMock()

    with patch.object(zipassist_init, "async_setup_frontend", setup_fe):
        await _async_register_frontend_card(hass)
        await _async_register_frontend_card(hass)

    assert hass.data[DOMAIN][DATA_FRONTEND_REGISTERED] is True
    setup_fe.assert_awaited_once()
    assert setup_fe.await_args.args[1] == _integration_version()


@pytest.mark.asyncio
async def test_async_setup_frontend_registers_static_path() -> None:
    """Card static path is registered under /zipassist; version is passed through."""
    from homeassistant.core import CoreState

    from custom_components.zipassist import frontend_register as fr

    hass = MagicMock()
    hass.data = {}
    hass.state = CoreState.running
    register = AsyncMock()
    # Dummy version proves passthrough without coupling to release bumps.
    dummy_version = "9.9.9-test"

    with patch.object(fr, "async_register_static_path", register), patch.object(
        fr, "async_init_lovelace_resource", AsyncMock()
    ) as init_res:
        await fr.async_setup_frontend(hass, dummy_version)

    register.assert_awaited_once()
    assert register.await_args.args[1] == "/zipassist"
    init_res.assert_awaited_once()
    assert init_res.await_args.args[1] == "/zipassist/zipassist-card.js"
    assert init_res.await_args.args[2] == dummy_version


def test_is_unsupported_storage_version_detects_ha_message() -> None:
    """Downgraded HA / newer lovelace_resources store is recognized."""
    from custom_components.zipassist.frontend_register import (
        _is_unsupported_storage_version,
    )

    class UnsupportedStorageVersionError(Exception):
        """Stand-in matching HA exception name."""

    err = UnsupportedStorageVersionError(
        "Storage file lovelace_resources has version 2 which is "
        "newer than the max supported version 1; upgrade Home "
        "Assistant or restore from a backup"
    )
    assert _is_unsupported_storage_version(err) is True
    assert _is_unsupported_storage_version(RuntimeError("other")) is False


@pytest.mark.asyncio
async def test_lovelace_resource_skips_unsupported_storage_version() -> None:
    """Storage version mismatch returns False without raising."""
    import sys
    from types import ModuleType

    from custom_components.zipassist import frontend_register as fr

    class UnsupportedStorageVersionError(Exception):
        """Stand-in matching HA's storage downgrade error."""

    add_js = MagicMock()
    fe_mod = ModuleType("homeassistant.components.frontend")
    fe_mod.add_extra_js_url = add_js  # type: ignore[attr-defined]
    comps = ModuleType("homeassistant.components")
    comps.frontend = fe_mod  # type: ignore[attr-defined]

    resources = MagicMock(spec=["async_get_info", "async_items"])
    resources.async_get_info = AsyncMock(
        side_effect=UnsupportedStorageVersionError(
            "Storage file lovelace_resources has version 2 which is "
            "newer than the max supported version 1"
        )
    )
    resources.async_items = MagicMock(return_value=[])
    hass = MagicMock()
    hass.data = {"lovelace": MagicMock(resources=resources)}

    with patch.dict(
        sys.modules,
        {
            "homeassistant.components": comps,
            "homeassistant.components.frontend": fe_mod,
        },
    ):
        ok = await fr.async_init_lovelace_resource(
            hass, "/zipassist/zipassist-card.js", "1.2.3"
        )

    assert ok is False
    add_js.assert_called_once()
    assert add_js.call_args.args[0] is hass
    assert add_js.call_args.args[1] == "/zipassist/zipassist-card.js?v=1.2.3"
    resources.async_items.assert_not_called()


def test_card_js_exists_and_defines_element() -> None:
    """Ship a card file that registers the custom element."""
    card = (
        _REPO_ROOT
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
    assert "KEY_ALIASES" in text
    assert "entityMatchesKey" in text
    assert "defaultCollapsed" in text
    assert "energy_daily_mon_on_active" in text
    assert "energy_monday_on_active" in text
    assert "TIMER_MODES" in text
    assert 'label: "Daily"' in text
    assert "&" + "amp;" in text
    assert "&" + "lt;" in text
    assert "&" + "gt;" in text
