"""The ZipAssist CMMS integration."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import ZipAssistClient
from .const import DEFAULT_BASE_URL, DOMAIN
from .coordinator import ZipAssistCoordinator
from .frontend_register import async_setup_frontend
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

# hass.data[DOMAIN] keys reserved for integration-level state (not entry ids)
DATA_FRONTEND_REGISTERED = "frontend_registered"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.TIME,
]


def _integration_version() -> str:
    """Return the integration version from manifest.json."""
    try:
        manifest_path = Path(__file__).with_name("manifest.json")
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        version = data.get("version")
        return str(version) if version else "0"
    except Exception:  # noqa: BLE001 - best-effort cache bust only
        return "0"


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the ZipAssist CMMS component."""
    hass.data.setdefault(DOMAIN, {})
    # Register Lovelace card once at component setup (not per config entry).
    await _async_register_frontend_card(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ZipAssist CMMS from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    client = ZipAssistClient(
        email=entry.data["email"],
        password=entry.data["password"],
        base_url=entry.data.get("base_url", DEFAULT_BASE_URL),
        session=session,
    )

    try:
        authenticated = await client.authenticate()
    except Exception as err:
        # Transient network/API failures should retry.
        raise ConfigEntryNotReady(f"Error connecting to ZipAssist: {err}") from err

    if not authenticated:
        raise ConfigEntryAuthFailed("Invalid ZipAssist credentials")

    coordinator = ZipAssistCoordinator(hass, client)
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        raise
    except Exception as err:
        # First refresh failures are usually connectivity; retry later.
        raise ConfigEntryNotReady(str(err)) from err

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services (idempotent)
    await async_setup_services(hass)

    # Listen for coordinator updates to detect auth failures
    @callback
    def _handle_coordinator_update() -> None:
        """Check for auth failures and trigger reauth if needed."""
        if not coordinator.last_update_success:
            last_ex = coordinator.last_exception
            if last_ex is not None:
                exc_str = str(last_ex).lower()
                if "401" in exc_str or "unauthorized" in exc_str or "auth" in exc_str:
                    _LOGGER.warning(
                        "Auth failure detected, starting reauth for %s",
                        entry.entry_id,
                    )
                    hass.async_create_task(
                        hass.config_entries.flow.async_init(
                            DOMAIN,
                            context={"source": "reauth", "entry_id": entry.entry_id},
                            data=dict(entry.data),
                        )
                    )

    entry.async_on_unload(
        coordinator.async_add_listener(_handle_coordinator_update)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id, None)
        if coordinator:
            # Shared HA session: close() is a no-op when session is not owned.
            await coordinator.client.close()
        # Only unload services if no more config entries remain.
        # Keep DATA_FRONTEND_REGISTERED so the card stays registered for the
        # lifetime of the HA process (static paths cannot be unregistered).
        remaining_entries = [
            key
            for key in hass.data.get(DOMAIN, {})
            if key != DATA_FRONTEND_REGISTERED
        ]
        if not remaining_entries:
            async_unload_services(hass)
    return bool(unload_ok)


async def _async_register_frontend_card(hass: HomeAssistant) -> None:
    """Register the ZipAssist frontend card so it auto-loads in the UI.

    Safe to call multiple times; registration is idempotent via a data flag.
    Uses the WebRTC-style pattern: static path + lovelace module resource +
    frontend extra module URL so the card appears in the picker reliably.
    """
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(DATA_FRONTEND_REGISTERED):
        return

    try:
        version = await hass.async_add_executor_job(_integration_version)
        await async_setup_frontend(hass, version)
        domain_data[DATA_FRONTEND_REGISTERED] = True
    except Exception:
        _LOGGER.exception("Failed to register ZipAssist frontend card")
