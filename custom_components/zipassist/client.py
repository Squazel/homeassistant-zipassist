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
        API_HYDROTAP_SEARCH_OPTIONS,
        API_OWNERS,
        API_SLEEP_MODES,
        API_SYSTEM_FAULTS,
        API_SYSTEM_EVENTS,
        API_COUNTRIES,
        API_TIMEZONES,
        DEFAULT_BASE_URL,
        DEFAULT_TIMEOUT,
    )
except ImportError:
    # Fallback for standalone testing without Home Assistant
    API_AUTH_LOGIN = "/api/auth/jwt/login"
    API_AUTH_REFRESH = "/api/auth/jwt/refresh"
    API_HYDROTAPS = "/api/hydrotaps"
    API_HYDROTAP_SEARCH_OPTIONS = "/api/hydrotap-search-options"
    API_OWNERS = "/api/owners"
    API_SLEEP_MODES = "/api/sleep-modes"
    API_SYSTEM_FAULTS = "/api/system-faults"
    API_SYSTEM_EVENTS = "/api/system-events"
    API_COUNTRIES = "/api/countries"
    API_TIMEZONES = "/api/timezones"
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


async def _safe_text(resp: aiohttp.ClientResponse) -> str:
    """Safely read response text, returning a truncated string."""
    try:
        text = await resp.text()
        return text[:500]
    except Exception:
        return "<unreadable>"


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
        self._user: dict[str, Any] = {}  # user info from auth response
        self._owner_id: str | None = None  # extracted from auth response

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
        """Login with HTTP Basic Auth, get JWT token.

        Also extracts user info (userType, ownerId) for routing
        subsequent API calls to the correct endpoint.
        """
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
                    # Extract user info for routing
                    inner = data.get("data", data)
                    self._user = inner.get("user", data.get("user", {}))
                    self._owner_id = (
                        self._user.get("owner", {}).get("ownerId")
                        or self._user.get("ownerId")
                    )
                    _LOGGER.debug(
                        "Token expires in %.0fs, userType=%s, ownerId=%s",
                        self._token_expiry - time.time(),
                        self._user.get("userType"),
                        self._owner_id,
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
        """Get all hydrotaps for the authenticated user.

        Uses the owner-specific endpoint when the user is an owner,
        falling back to the admin endpoint if that fails.
        """
        user_type = self._user.get("userType", "")

        # Try owner-specific endpoint first
        if user_type == "owner" and self._owner_id:
            data = await self._get(
                f"{API_OWNERS}/{self._owner_id}/hydrotaps"
            )
            if isinstance(data, list):
                return data
            _LOGGER.debug(
                "Owner endpoint returned non-list, falling back to /api/hydrotaps"
            )

        # Fall back to admin endpoint
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
        headers = {
            **self._auth_headers,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        async with session.patch(
            url, headers=headers, json=settings
        ) as resp:
            if resp.status in (200, 204):
                return True
            if resp.status == 401:
                _LOGGER.debug("PATCH 401 — re-authenticating and retrying")
                await self.authenticate()
                retry_headers = {
                    **self._auth_headers,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
                async with session.patch(
                    url, headers=retry_headers, json=settings
                ) as retry_resp:
                    if retry_resp.status in (200, 204):
                        return True
                    _LOGGER.error(
                        "PATCH retry failed: %s — %s",
                        retry_resp.status,
                        await _safe_text(retry_resp),
                    )
                    return False
            _LOGGER.error(
                "PATCH failed: %s — %s",
                resp.status,
                await _safe_text(resp),
            )
            return False

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

    async def clear_fault(
        self, hydrotap_id: str, fault_id: str, end_timestamp: str
    ) -> bool:
        """Clear a system fault by setting its end timestamp."""
        await self._ensure_fresh_token()
        url = (
            f"{self._base_url}{API_HYDROTAPS}/{hydrotap_id}"
            f"/system-faults/{fault_id}"
        )
        session = await self._get_session()
        payload = {"endTimestamp": end_timestamp}
        async with session.patch(
            url, headers=self._auth_headers, json=payload
        ) as resp:
            if resp.status == 401:
                _LOGGER.debug("PATCH fault 401 — re-authenticating and retrying")
                await self.authenticate()
                async with session.patch(
                    url, headers=self._auth_headers, json=payload
                ) as retry_resp:
                    return retry_resp.status == 200
            return resp.status == 200

    # -------------------------------------------------------- timezone

    async def get_timezone(self, hydrotap_id: str) -> dict[str, Any] | None:
        """Get timezone for a hydrotap."""
        result = await self._get(
            f"{API_HYDROTAPS}/{hydrotap_id}/timezone"
        )
        return result if isinstance(result, dict) else None

    # -------------------------------------------------- filter usage logs

    async def get_filter_usage(
        self,
        hydrotap_id: str,
        page: int = 0,
        per_page: int = 10,
        filter_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get filter usage history for a hydrotap."""
        params = f"page={page}&perPage={per_page}"
        if filter_type:
            params += f"&type={filter_type}"
        data = await self._get(
            f"{API_HYDROTAPS}/{hydrotap_id}/logs/filter-usage?{params}"
        )
        return data if isinstance(data, list) else []

    # ----------------------------------------------- dispense event logs

    async def get_dispense_events(
        self, hydrotap_id: str, page: int = 0, per_page: int = 10
    ) -> list[dict[str, Any]]:
        """Get dispense event history for a hydrotap."""
        data = await self._get(
            f"{API_HYDROTAPS}/{hydrotap_id}/logs/dispense-events"
            f"?page={page}&perPage={per_page}"
        )
        return data if isinstance(data, list) else []

    # ---------------------------------------------------- daily usage

    async def get_daily_usage(
        self, hydrotap_id: str
    ) -> dict[str, Any] | None:
        """Get daily usage summary for a hydrotap."""
        result = await self._get(
            f"{API_HYDROTAPS}/{hydrotap_id}/logs/daily-usage?limit=1"
        )
        if isinstance(result, list) and result:
            item = result[0]
            return item if isinstance(item, dict) else None
        return None

    # ------------------------------------------------- water/energy usage

    async def get_water_usage(
        self,
        hydrotap_id: str,
        min_date: str,
        max_date: str,
        timezone_offset: int = 0,
    ) -> dict[str, Any] | None:
        """Get water usage data for a hydrotap."""
        result = await self._get(
            f"{API_HYDROTAPS}/{hydrotap_id}/usage/water"
            f"?minDate={min_date}&maxDate={max_date}&timezoneOffset={timezone_offset}"
        )
        return result if isinstance(result, dict) else None

    async def get_energy_usage(
        self,
        hydrotap_id: str,
        min_date: str,
        max_date: str,
        timezone_offset: int = 0,
    ) -> dict[str, Any] | None:
        """Get energy usage data for a hydrotap."""
        result = await self._get(
            f"{API_HYDROTAPS}/{hydrotap_id}/usage/energy"
            f"?minDate={min_date}&maxDate={max_date}&timezoneOffset={timezone_offset}"
        )
        return result if isinstance(result, dict) else None

    # ---------------------------------------------------- usage graphs

    async def get_usage_graph(
        self,
        hydrotap_id: str,
        min_date: str,
        max_date: str,
        timezone_offset: int = 0,
    ) -> dict[str, Any] | None:
        """Get usage graph series data for a hydrotap."""
        result = await self._get(
            f"{API_HYDROTAPS}/{hydrotap_id}/graphs/usage"
            f"?minDate={min_date}&maxDate={max_date}&timezoneOffset={timezone_offset}"
        )
        return result if isinstance(result, dict) else None

    async def get_average_usage_graph(
        self,
        hydrotap_id: str,
        min_date: str,
        max_date: str,
        timezone_offset: int = 0,
    ) -> dict[str, Any] | None:
        """Get average usage graph data for a hydrotap."""
        result = await self._get(
            f"{API_HYDROTAPS}/{hydrotap_id}/graphs/average-usage"
            f"?minDate={min_date}&maxDate={max_date}&timezoneOffset={timezone_offset}"
        )
        return result if isinstance(result, dict) else None

    # ---------------------------------------------- fault/event definitions

    async def get_system_faults(self) -> list[dict[str, Any]]:
        """Get system fault code definitions."""
        data = await self._get(API_SYSTEM_FAULTS)
        return data if isinstance(data, list) else []

    async def get_system_events(self) -> list[dict[str, Any]]:
        """Get system event definitions."""
        data = await self._get(API_SYSTEM_EVENTS)
        return data if isinstance(data, list) else []

    # ------------------------------------------------------- sleep modes

    async def get_sleep_modes(
        self, sleep_mode_id: str | None = None
    ) -> list[dict[str, Any]] | dict[str, Any] | None:
        """Get available sleep mode options.

        If sleep_mode_id is provided, returns a single dict.
        Otherwise returns a list of all sleep modes.
        """
        path = (
            f"{API_SLEEP_MODES}/{sleep_mode_id}"
            if sleep_mode_id
            else API_SLEEP_MODES
        )
        result = await self._get(path)
        return result if isinstance(result, (dict, list)) else None

    # --------------------------------------------------- reference data

    async def get_countries(self) -> list[dict[str, Any]]:
        """Get list of countries."""
        data = await self._get(API_COUNTRIES)
        return data if isinstance(data, list) else []

    async def get_timezones(self) -> list[dict[str, Any]]:
        """Get list of timezones."""
        data = await self._get(API_TIMEZONES)
        return data if isinstance(data, list) else []

    # ------------------------------------------------------------ notes

    async def get_notes(self, hydrotap_id: str) -> list[dict[str, Any]]:
        """Get admin notes for a hydrotap."""
        data = await self._get(
            f"{API_HYDROTAPS}/{hydrotap_id}/notes"
        )
        return data if isinstance(data, list) else []

    async def add_note(
        self, hydrotap_id: str, note: dict[str, Any]
    ) -> bool:
        """Add a note to a hydrotap."""
        await self._ensure_fresh_token()
        url = f"{self._base_url}{API_HYDROTAPS}/{hydrotap_id}/notes"
        session = await self._get_session()
        async with session.post(
            url, headers=self._auth_headers, json=note
        ) as resp:
            if resp.status == 401:
                _LOGGER.debug("POST note 401 — re-authenticating and retrying")
                await self.authenticate()
                async with session.post(
                    url, headers=self._auth_headers, json=note
                ) as retry_resp:
                    return retry_resp.status in (200, 201)
            return resp.status in (200, 201)

    # --------------------------------------------------- admin search

    async def get_hydrotap_search_options(self) -> dict[str, Any] | None:
        """Get hydrotap search filter metadata."""
        result = await self._get(API_HYDROTAP_SEARCH_OPTIONS)
        return result if isinstance(result, dict) else None

    # ----------------------------------------------- owner dashboards

    async def get_owner_hydrotap_groups(
        self, owner_id: str
    ) -> list[dict[str, Any]]:
        """Get hydrotap groups for an owner."""
        data = await self._get(
            f"{API_OWNERS}/{owner_id}/hydrotap-groups"
        )
        return data if isinstance(data, list) else []

    async def get_owner_faults_major(
        self, owner_id: str
    ) -> dict[str, Any] | None:
        """Get major fault dashboard data for an owner."""
        result = await self._get(
            f"{API_OWNERS}/{owner_id}/hydrotap-system-faults/major"
        )
        return result if isinstance(result, dict) else None

    async def get_owner_faults_minor(
        self, owner_id: str
    ) -> dict[str, Any] | None:
        """Get minor fault/alert dashboard data for an owner."""
        result = await self._get(
            f"{API_OWNERS}/{owner_id}/hydrotap-system-faults/minor"
        )
        return result if isinstance(result, dict) else None

    async def get_owner_hydrotaps_no_faults(
        self, owner_id: str
    ) -> list[dict[str, Any]]:
        """Get hydrotaps without system faults for an owner."""
        data = await self._get(
            f"{API_OWNERS}/{owner_id}/hydrotaps-without-system-faults"
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