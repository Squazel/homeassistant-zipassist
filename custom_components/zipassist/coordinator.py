"""DataUpdateCoordinator for ZipAssist CMMS."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import ZipAssistClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ZipAssistCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching data from ZipAssist CMMS."""

    def __init__(self, hass: HomeAssistant, client: ZipAssistClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from ZipAssist CMMS.

        Returns a dict with:
          - hydrotaps: list of hydrotap dicts (from list endpoint, has sensor data)
          - settings: dict of {hydrotapId: settings_dict}
          - settings_options: dict of {hydrotapId: settings_options_dict}
        """
        try:
            hydrotaps = await self.client.get_hydrotaps()
            _LOGGER.debug("Fetched %d hydrotaps", len(hydrotaps))

            settings: dict[str, dict[str, Any]] = {}
            settings_options: dict[str, dict[str, Any]] = {}

            for h in hydrotaps:
                hid = h.get("hydrotapId")
                if not hid:
                    continue
                try:
                    s = await self.client.get_settings(hid)
                    if s:
                        settings[hid] = s
                except Exception:
                    _LOGGER.debug("Failed to fetch settings for %s", hid, exc_info=True)

                try:
                    so = await self.client.get_settings_options(hid)
                    if so:
                        settings_options[hid] = so
                except Exception:
                    _LOGGER.debug(
                        "Failed to fetch settings-options for %s", hid, exc_info=True
                    )

            return {
                "hydrotaps": hydrotaps,
                "settings": settings,
                "settings_options": settings_options,
            }
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err