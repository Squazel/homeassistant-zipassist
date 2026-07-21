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


def _is_unsupported_storage_version(err: BaseException) -> bool:
    """True when HA cannot read lovelace_resources (store newer than core)."""
    # Prefer the real HA exception when the installed core exposes a real type.
    # (Some test stubs put a non-type mock on homeassistant.exceptions.)
    try:
        from homeassistant.exceptions import UnsupportedStorageVersionError as Exc
    except ImportError:  # pragma: no cover - very old cores
        Exc = None  # type: ignore[assignment,misc]
    else:
        if isinstance(Exc, type) and issubclass(Exc, BaseException):
            if isinstance(err, Exc):
                return True

    # Message match covers renamed exceptions and stubbed HA packages.
    msg = str(err).lower()
    name = type(err).__name__.lower()
    if "unsupportedstorageversion" in name:
        return True
    return "lovelace_resources" in msg and (
        "unsupported" in msg or "newer than the max supported" in msg
    )


async def async_init_lovelace_resource(
    hass: HomeAssistant, url: str, version: str
) -> bool:
    """Ensure the card is loaded as a Lovelace module resource.

    Mirrors AlexxIT/WebRTC:
    - always add_extra_js_url (module)
    - storage mode: create/update lovelace resource (res_type=module)

    Returns True if a lovelace resource was created/updated.

    Note: ``add_extra_js_url`` alone is enough for the card to load. Writing
    the Lovelace resource collection is best-effort. If this HA core cannot
    read ``lovelace_resources`` (storage version newer than the core supports
    — typically a downgrade or partial restore), we skip storage writes and
    rely on the extra JS URL. That is not a ZipAssist card syntax error.
    """
    url2 = f"{url}?v={version}"
    # Extra JS may already be registered by async_setup_frontend; keep idempotent.
    _try_add_extra_js(hass, url2)

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
    except Exception as err:  # noqa: BLE001
        if _is_unsupported_storage_version(err):
            # Common after HA downgrade / restore of a newer .storage file.
            # Card still loads via add_extra_js_url; do not spam a full traceback.
            _LOGGER.warning(
                "Skipping Lovelace resource write: this Home Assistant core "
                "cannot read lovelace_resources storage (%s). The ZipAssist "
                "card is still registered via frontend extra JS. Upgrade HA "
                "to match the storage file, or restore a matching backup. "
                "This is not a ZipAssist card syntax/logic error.",
                err,
            )
        else:
            _LOGGER.warning(
                "Lovelace resource registration failed (card may still load "
                "via extra JS)",
                exc_info=True,
            )

    return False


def _try_add_extra_js(hass: HomeAssistant, url: str) -> bool:
    """Register frontend extra module URL (best-effort)."""
    try:
        from homeassistant.components.frontend import add_extra_js_url

        add_extra_js_url(hass, url, es5=False)
        _LOGGER.debug("Registered extra JS module: %s", url)
        return True
    except Exception:  # noqa: BLE001
        _LOGGER.warning("add_extra_js_url failed for %s", url, exc_info=True)
        return False


async def async_setup_frontend(hass: HomeAssistant, version: str) -> None:
    """Serve the card and register it with the frontend / Lovelace."""
    frontend_dir = Path(__file__).parent / "frontend"
    card_file = frontend_dir / CARD_FILENAME
    if not card_file.exists():
        _LOGGER.warning("ZipAssist card missing at %s", card_file)
        return

    url2 = f"{CARD_URL_PATH}?v={version}"

    # Serve frontend directory under /zipassist/.
    # cache_headers=False avoids sticky browser caches of older card builds when
    # the ?v= query is stripped by proxies; version query still used for busting.
    await async_register_static_path(
        hass, "/zipassist", str(frontend_dir), cache_headers=False
    )

    # Always register extra JS as early as possible so the dashboard does not
    # race a late HOMEASSISTANT_STARTED listener. Lovelace resource write is
    # separate and may fail on broken lovelace_resources storage.
    _try_add_extra_js(hass, url2)

    async def _register_resource(_event: Event | None = None) -> None:
        # Re-assert extra JS after start (frontend component fully up).
        _try_add_extra_js(hass, url2)
        ok = await async_init_lovelace_resource(hass, CARD_URL_PATH, version)
        if ok:
            _LOGGER.info(
                "ZipAssist card Lovelace resource ready at %s",
                url2,
            )
        else:
            _LOGGER.info(
                "ZipAssist card served at %s via frontend extra JS "
                "(Lovelace resource not written — YAML mode, storage not "
                "ready, or lovelace_resources version mismatch). If the card "
                "shows 'custom element doesn't exist', hard-refresh once or "
                "add a Lovelace resource manually: %s (type: module).",
                url2,
                url2,
            )

    # Lovelace storage is often not ready during early async_setup.
    if hass.state is CoreState.running:
        await _register_resource()
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _register_resource)

    _LOGGER.info("ZipAssist card static path registered at %s", CARD_URL_PATH)
