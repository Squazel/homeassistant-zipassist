"""The ZipAssist CMMS integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.update_coordinator import UpdateFailed

try:
    from homeassistant.components.frontend import add_extra_js_url
    from homeassistant.components.http import StaticPathConfig
    FRONTEND_AVAILABLE = True
except ImportError:
    FRONTEND_AVAILABLE = False

from .client import ZipAssistClient
from .const import DEFAULT_BASE_URL, DOMAIN
from .coordinator import ZipAssistCoordinator
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.TIME,
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the ZipAssist CMMS component."""
    hass.data.setdefault(DOMAIN, {})
    await _async_register_frontend_card(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ZipAssist CMMS from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    client = ZipAssistClient(
        email=entry.data["email"],
        password=entry.data["password"],
        base_url=entry.data.get("base_url", DEFAULT_BASE_URL),
    )

    if not await client.authenticate():
        _LOGGER.error("Failed to authenticate with ZipAssist")
        return False

    coordinator = ZipAssistCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services (only once, not per entry)
    await async_setup_services(hass)

    # Listen for coordinator updates to detect auth failures
    @callback
    def _handle_coordinator_update() -> None:
        """Check for auth failures and trigger reauth if needed."""
        if not coordinator.last_update_success:
            # Check if the failure was due to auth
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
                            data=entry,
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
            await coordinator.client.close()
        # Only unload services if no more entries
        if not hass.data[DOMAIN]:
            async_unload_services(hass)
    return unload_ok


async def _async_register_frontend_card(hass: HomeAssistant) -> None:
    """Register the ZipAssist frontend card so it auto-loads in the UI."""
    if not FRONTEND_AVAILABLE:
        return

    try:
        frontend_path = Path(__file__).parent / "frontend"
        card_file = frontend_path / "zipassist-card.js"

        if not card_file.exists():
            _LOGGER.warning(
                "ZipAssist frontend card file not found at %s", card_file
            )
            return

        await hass.http.async_register_static_paths([
            StaticPathConfig(
                f"/{DOMAIN}",
                str(frontend_path),
                cache_headers=False,
            )
        ])

        card_url = f"/{DOMAIN}/zipassist-card.js"
        add_extra_js_url(hass, card_url)

        _LOGGER.debug("ZipAssist frontend card registered at %s", card_url)
    except Exception:
        _LOGGER.exception("Failed to register ZipAssist frontend card")