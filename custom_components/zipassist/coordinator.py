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
        self.hydrotaps: list[dict[str, Any]] = []

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from ZipAssist CMMS."""
        try:
            self.hydrotaps = await self.client.get_hydrotaps()
            _LOGGER.debug("Fetched %d hydrotaps", len(self.hydrotaps))
            return {"hydrotaps": self.hydrotaps}
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err