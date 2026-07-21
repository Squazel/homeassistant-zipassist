"""Frontend / Lovelace card registration for ZipAssist."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.core import HomeAssistant

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
        # Older HA
        hass.http.register_static_path(url_path, path)


async def async_init_lovelace_resource(
    hass: HomeAssistant, url: str, version: str
) -> None:
    """Ensure the card is loaded as a Lovelace module resource.

    Mirrors the proven AlexxIT/WebRTC pattern:
    - storage mode: create/update a lovelace resource (res_type=module)
    - YAML mode / always: also add_extra_js_url as a module
    """
    url2 = f"{url}?v={version}"

    # Always register as frontend extra module (works without lovelace storage).
    try:
        from homeassistant.components.frontend import add_extra_js_url

        add_extra_js_url(hass, url2, es5=False)
        _LOGGER.debug("Registered extra JS module: %s", url2)
    except Exception:  # noqa: BLE001
        _LOGGER.debug("add_extra_js_url unavailable", exc_info=True)

    # Best-effort Lovelace resource registration (storage dashboards).
    try:
        lovelace = hass.data.get("lovelace")
        if lovelace is None:
            return

        resources = (
            lovelace.resources
            if hasattr(lovelace, "resources")
            else lovelace.get("resources")  # type: ignore[union-attr]
        )
        if resources is None:
            return

        # Cast to collection-like
        if hasattr(resources, "async_get_info"):
            await resources.async_get_info()

        items = list(resources.async_items()) if hasattr(resources, "async_items") else []
        for item in items:
            item_url = str(item.get("url", ""))
            if item_url.startswith(url) or CARD_FILENAME in item_url:
                # Update existing resource to current versioned URL
                if hasattr(resources, "async_update_item"):
                    await resources.async_update_item(
                        item["id"], {"res_type": "module", "url": url2}
                    )
                    _LOGGER.debug("Updated lovelace resource to %s", url2)
                return

        if hasattr(resources, "async_create_item"):
            await resources.async_create_item({"res_type": "module", "url": url2})
            _LOGGER.debug("Created lovelace resource %s", url2)
    except Exception:  # noqa: BLE001
        # Lovelace may not be ready yet; extra_js_url still covers most installs.
        _LOGGER.debug("Lovelace resource registration skipped", exc_info=True)


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
    await async_init_lovelace_resource(hass, CARD_URL_PATH, version)
    _LOGGER.info("ZipAssist card available at %s?v=%s", CARD_URL_PATH, version)
