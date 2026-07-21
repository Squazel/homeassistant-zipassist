"""Frontend / Lovelace card registration for ZipAssist."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, Event, HomeAssistant

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "zipassist-card.js"
CARD_URL_PATH = "/zipassist/zipassist-card.js"


async def async_register_static_path(
    hass: HomeAssistant, url_path: str, path: str, cache_headers: bool = True
) -> None:
    """Register a static path (HA 2024.7+ API with fallback)."""
    try:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(url_path, path, cache_headers)]
        )
    except Exception:  # noqa: BLE001
        hass.http.register_static_path(url_path, path)


async def async_init_lovelace_resource(
    hass: HomeAssistant, url: str, version: str
) -> bool:
    """Ensure the card is loaded as a Lovelace module resource.

    Mirrors AlexxIT/WebRTC:
    - always add_extra_js_url (module)
    - storage mode: create/update lovelace resource (res_type=module)

    Returns True if a lovelace resource was created/updated.
    """
    url2 = f"{url}?v={version}"
    resource_ok = False

    try:
        from homeassistant.components.frontend import add_extra_js_url

        add_extra_js_url(hass, url2, es5=False)
        _LOGGER.debug("Registered extra JS module: %s", url2)
    except Exception:  # noqa: BLE001
        _LOGGER.warning("add_extra_js_url failed for %s", url2, exc_info=True)

    try:
        lovelace = hass.data.get("lovelace")
        if lovelace is None:
            _LOGGER.debug("lovelace not in hass.data yet")
            return False

        resources = (
            lovelace.resources
            if hasattr(lovelace, "resources")
            else lovelace["resources"]  # type: ignore[index]
        )

        # Force load storage collection (required before async_items).
        if hasattr(resources, "async_get_info"):
            await resources.async_get_info()

        items = (
            list(resources.async_items())
            if hasattr(resources, "async_items")
            else []
        )
        for item in items:
            item_url = str(item.get("url", ""))
            if not (
                item_url.startswith(url)
                or CARD_FILENAME in item_url
                or "/zipassist/" in item_url
            ):
                continue

            if item_url.endswith(version) or f"v={version}" in item_url:
                _LOGGER.debug("Lovelace resource already current: %s", item_url)
                return True

            if hasattr(resources, "async_update_item"):
                await resources.async_update_item(
                    item["id"], {"res_type": "module", "url": url2}
                )
                _LOGGER.info("Updated Lovelace resource to %s", url2)
                return True

            item["url"] = url2
            return True

        if hasattr(resources, "async_create_item"):
            await resources.async_create_item({"res_type": "module", "url": url2})
            _LOGGER.info("Created Lovelace resource %s", url2)
            return True

        _LOGGER.debug("Lovelace resources collection has no create/update API")
    except Exception:  # noqa: BLE001
        _LOGGER.warning(
            "Lovelace resource registration failed (will retry if possible)",
            exc_info=True,
        )

    return resource_ok


async def async_setup_frontend(hass: HomeAssistant, version: str) -> None:
    """Serve the card and register it with the frontend / Lovelace."""
    frontend_dir = Path(__file__).parent / "frontend"
    card_file = frontend_dir / CARD_FILENAME
    if not card_file.exists():
        _LOGGER.warning("ZipAssist card missing at %s", card_file)
        return

    # Serve entire frontend directory under /zipassist/
    await async_register_static_path(
        hass, "/zipassist", str(frontend_dir), cache_headers=True
    )

    async def _register_resource(_event: Event | None = None) -> None:
        ok = await async_init_lovelace_resource(hass, CARD_URL_PATH, version)
        if ok:
            _LOGGER.info(
                "ZipAssist card Lovelace resource ready at %s?v=%s",
                CARD_URL_PATH,
                version,
            )
        else:
            _LOGGER.info(
                "ZipAssist card served at %s?v=%s (extra JS); "
                "Lovelace resource pending or YAML mode",
                CARD_URL_PATH,
                version,
            )

    # Lovelace storage is often not ready during early async_setup.
    if hass.state is CoreState.running:
        await _register_resource()
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _register_resource)
        # Still register extra JS immediately when possible
        try:
            from homeassistant.components.frontend import add_extra_js_url

            add_extra_js_url(hass, f"{CARD_URL_PATH}?v={version}", es5=False)
        except Exception:  # noqa: BLE001
            pass

    _LOGGER.info("ZipAssist card static path registered at %s", CARD_URL_PATH)
