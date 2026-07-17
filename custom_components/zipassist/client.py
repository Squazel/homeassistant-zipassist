"""ZipAssist CMMS API client."""

from __future__ import annotations

import base64
import json
import logging
import time
from typing import Any

import aiohttp

try:
    from .const import (
        API_AUTH_LOGIN,
        API_AUTH_REFRESH,
        API_HYDROTAPS,
        DEFAULT_BASE_URL,
        DEFAULT_TIMEOUT,
    )
except ImportError:
    # Fallback for standalone testing without Home Assistant
    API_AUTH_LOGIN = "/api/auth/jwt/login"
    API_AUTH_REFRESH = "/api/auth/jwt/refresh"
    API_HYDROTAPS = "/api/hydrotaps"
    DEFAULT_BASE_URL = "https://zipassist.zipindustries.com"
    DEFAULT_TIMEOUT = 30

_LOGGER = logging.getLogger(__name__)

# Refresh token when fewer than this many seconds remain before expiry
_TOKEN_REFRESH_MARGIN = 300  # 5 minutes


def _jwt_expiry(token: str) -> float:
    """Extract the 'exp' claim from a JWT (seconds since epoch), or 0 if unparseable."""
    try:
        payload_b64 = token.split(".")[1]
        # Add padding if needed
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return float(payload.get("exp", 0))
    except (IndexError, ValueError, json.JSONDecodeError):
        return 0


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
        self._token_expiry: float = 0  # epoch seconds

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

    @property
    def _token_expiring_soon(self) -> bool:
        """True if the token is missing or will expire within the margin."""
        if not self._token:
            return True
        return time.time() + _TOKEN_REFRESH_MARGIN >= self._token_expiry

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
                if self._token:
                    self._token_expiry = _jwt_expiry(self._token)
                    _LOGGER.debug(
                        "Token expires in %.0fs",
                        self._token_expiry - time.time(),
                    )
                    return True
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
                    self._token_expiry = _jwt_expiry(new_token)
                    _LOGGER.debug("Token refreshed")
                    return True
            _LOGGER.debug("Token refresh failed: %s", resp.status)
            return False

    async def _ensure_fresh_token(self) -> None:
        """Refresh or re-authenticate if the token is near expiry."""
        if not self._token_expiring_soon:
            return
        if self._token and await self.refresh_token():
            return
        # Refresh failed or no token — full re-auth
        _LOGGER.debug("Re-authenticating (token expired or missing)")
        await self.authenticate()

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
        await self._ensure_fresh_token()
        url = f"{self._base_url}{API_HYDROTAPS}/{hydrotap_id}/settings"
        session = await self._get_session()
        async with session.patch(
            url, headers=self._auth_headers, json=settings
        ) as resp:
            if resp.status == 401:
                _LOGGER.debug("PATCH 401 — re-authenticating and retrying")
                await self.authenticate()
                async with session.patch(
                    url, headers=self._auth_headers, json=settings
                ) as retry_resp:
                    return retry_resp.status == 200
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

    async def _get(
        self, path: str
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        """GET an API path, return parsed JSON or None.

        Automatically refreshes the token before the call if near expiry,
        and retries once on 401.
        """
        await self._ensure_fresh_token()

        url = f"{self._base_url}{path}"
        session = await self._get_session()
        async with session.get(url, headers=self._auth_headers) as resp:
            if resp.status == 401:
                _LOGGER.debug("GET %s → 401, re-authenticating", path)
                if await self.authenticate():
                    async with session.get(
                        url, headers=self._auth_headers
                    ) as retry_resp:
                        if (
                            retry_resp.status == 200
                            and "json" in (retry_resp.content_type or "")
                        ):
                            return await retry_resp.json()
                return None
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