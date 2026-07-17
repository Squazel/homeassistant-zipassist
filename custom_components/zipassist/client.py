"""ZipAssist CMMS API client."""

from __future__ import annotations

import base64
import logging
from typing import Any

import aiohttp

from .const import (
    API_AUTH_LOGIN,
    API_AUTH_REFRESH,
    API_HYDROTAPS,
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class ZipAssistClient:
    """Client for interacting with the ZipAssist CMMS API."""

    def __init__(
        self,
        email: str,
        password: str,
        base_url: str = DEFAULT_BASE_URL,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize the client."""
        self._email = email
        self._password = password
        self._base_url = base_url.rstrip("/")
        self._session = session
        self._own_session = False
        self._token: str | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an HTTP session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._own_session = True
        return self._session

    @property
    def _auth_headers(self) -> dict[str, str]:
        """Return Authorization header if we have a token."""
        if self._token:
            return {"Authorization": f"Bearer {self._token}"}
        return {}

    # ---------------------------------------------------------------- auth

    async def authenticate(self) -> bool:
        """Login with HTTP Basic Auth, get JWT token."""
        credentials = base64.b64encode(
            f"{self._email}:{self._password}".encode()
        ).decode()
        url = f"{self._base_url}{API_AUTH_LOGIN}"
        session = await self._get_session()

        _LOGGER.debug("Authenticating to %s", url)
        async with session.get(
            url,
            headers={"Authorization": f"Basic {credentials}"},
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                self._token = data.get("token")
                return self._token is not None
            _LOGGER.error("Auth failed: %s", resp.status)
            return False

    async def refresh_token(self) -> bool:
        """Refresh the JWT token."""
        if not self._token:
            return False
        url = f"{self._base_url}{API_AUTH_REFRESH}"
        session = await self._get_session()
        async with session.get(url, headers=self._auth_headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                new_token = data.get("token")
                if new_token:
                    self._token = new_token
                    return True
            return False

    # --------------------------------------------------------------- hydrotaps

    async def get_hydrotaps(self) -> list[dict[str, Any]]:
        """Get all hydrotaps for the authenticated user."""
        data = await self._get(f"{API_HYDROTAPS}")
        return data if isinstance(data, list) else []

    async def get_hydrotap(self, hydrotap_id: str) -> dict[str, Any] | None:
        """Get a single hydrotap detail."""
        result = await self._get(f"{API_HYDROTAPS}/{hydrotap_id}")
        return result if isinstance(result, dict) else None

    async def get_settings(self, hydrotap_id: str) -> dict[str, Any] | None:
        """Get settings for a hydrotap."""
        result = await self._get(f"{API_HYDROTAPS}/{hydrotap_id}/settings")
        return result if isinstance(result, dict) else None

    async def get_settings_options(self, hydrotap_id: str) -> dict[str, Any] | None:
        """Get settings options (ranges/choices) for a hydrotap."""
        result = await self._get(
            f"{API_HYDROTAPS}/{hydrotap_id}/settings-options"
        )
        return result if isinstance(result, dict) else None

    async def update_settings(
        self, hydrotap_id: str, settings: dict[str, Any]
    ) -> bool:
        """Update settings for a hydrotap (PATCH)."""
        url = f"{self._base_url}{API_HYDROTAPS}/{hydrotap_id}/settings"
        session = await self._get_session()
        async with session.patch(url, headers=self._auth_headers, json=settings) as resp:
            return resp.status == 200

    # ------------------------------------------------------------------ logs

    async def get_status_logs(
        self, hydrotap_id: str, page: int = 0, per_page: int = 10
    ) -> list[dict[str, Any]]:
        data = await self._get(
            f"{API_HYDROTAPS}/{hydrotap_id}/logs/general?page={page}&perPage={per_page}"
        )
        return data if isinstance(data, list) else []

    async def get_latest_log(self, hydrotap_id: str) -> dict[str, Any] | None:
        """Get the latest status log with smart estimate."""
        result = await self._get(
            f"{API_HYDROTAPS}/{hydrotap_id}/logs/general?limit=1&withSmartEstimate=true"
        )
        if isinstance(result, list) and result:
            item = result[0]
            return item if isinstance(item, dict) else None
        return None

    async def get_current_faults(
        self, hydrotap_id: str
    ) -> list[dict[str, Any]]:
        data = await self._get(
            f"{API_HYDROTAPS}/{hydrotap_id}/logs/system-faults?currentOnly=true"
        )
        return data if isinstance(data, list) else []

    # ------------------------------------------------------------------ fetch

    async def _get(self, path: str) -> dict[str, Any] | list[dict[str, Any]] | None:
        """GET an API path, return parsed JSON or None."""
        url = f"{self._base_url}{path}"
        session = await self._get_session()
        async with session.get(url, headers=self._auth_headers) as resp:
            if resp.status == 200 and "json" in (resp.content_type or ""):
                return await resp.json()
            _LOGGER.debug("GET %s → %s", url, resp.status)
            return None

    # ------------------------------------------------------------------ lifecycle

    async def close(self) -> None:
        """Close the client session."""
        if self._own_session and self._session is not None:
            await self._session.close()
            self._session = None
            self._own_session = False