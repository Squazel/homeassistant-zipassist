"""Exploration script for discovering the ZipAssist CMMS API.

API structure discovered from the AngularJS frontend bundle (zip-hydrotap-code.js).

Auth flow:
  1. GET /api/auth/jwt/login  with Authorization: Basic <b64(email:password)>
  2. Response contains a JWT {token, user}
  3. All subsequent requests use Authorization: Bearer <token>
  4. Refresh via GET /api/auth/jwt/refresh

Usage:
    python exploration/explore.py
    python exploration/explore.py --endpoints-only
    python exploration/explore.py --base-url https://custom.example.com
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import logging
import os
import sys
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname).4s] %(name)s: %(message)s",
)
_LOGGER = logging.getLogger("explore")


# ------------------------------------------------------------------ endpoint registry

# All known API endpoints, grouped by category.
# This is the canonical list — used by --endpoints-only and for validation.
KNOWN_ENDPOINTS: dict[str, list[tuple[str, str, str]]] = {
    "Auth": [
        ("GET", "/api/auth/jwt/login", "Login (Basic auth)"),
        ("GET", "/api/auth/jwt/refresh", "Refresh JWT token"),
    ],
    "Hydrotap Listing": [
        ("GET", "/api/hydrotaps", "Search all hydrotaps (admin)"),
        ("GET", "/api/owners/{ownerId}/hydrotaps", "List owner's hydrotaps"),
        ("GET", "/api/owners/{ownerId}/hydrotaps-without-system-faults", "Taps without alerts"),
    ],
    "Hydrotap Detail & Settings": [
        ("GET", "/api/hydrotaps/{id}", "Hydrotap detail"),
        ("GET", "/api/hydrotaps/{id}/settings", "Current settings"),
        ("GET", "/api/hydrotaps/{id}/settings-options", "Allowed ranges/options"),
        ("PATCH", "/api/hydrotaps/{id}/settings", "Write settings"),
        ("GET", "/api/hydrotaps/{id}/timezone", "Timezone"),
    ],
    "Logs & Usage": [
        ("GET", "/api/hydrotaps/{id}/logs/general", "Status logs"),
        ("GET", "/api/hydrotaps/{id}/logs/system-faults", "Active system faults"),
        ("GET", "/api/hydrotaps/{id}/logs/filter-usage", "Filter usage history"),
        ("GET", "/api/hydrotaps/{id}/logs/dispense-events", "Dispense events"),
        ("GET", "/api/hydrotaps/{id}/logs/daily-usage", "Daily usage summary"),
        ("GET", "/api/hydrotaps/{id}/usage/water", "Water usage data"),
        ("GET", "/api/hydrotaps/{id}/usage/energy", "Energy usage data"),
        ("GET", "/api/hydrotaps/{id}/graphs/usage", "Graph series data"),
        ("GET", "/api/hydrotaps/{id}/graphs/average-usage", "Average usage graph"),
    ],
    "Faults & Alerts": [
        ("GET", "/api/system-faults", "Fault code definitions"),
        ("GET", "/api/system-events", "System event definitions"),
        ("PATCH", "/api/hydrotaps/{id}/system-faults/{faultId}", "Clear a fault"),
    ],
    "Hydrotap Search (Admin)": [
        ("GET", "/api/hydrotaps", "Search all hydrotaps (paginated)"),
        ("GET", "/api/hydrotap-search-options", "Filter option metadata"),
    ],
    "Owner-specific": [
        ("GET", "/api/owners/{ownerId}/hydrotaps", "List owner's hydrotaps"),
        ("GET", "/api/owners/{ownerId}/hydrotap-groups", "Owner's groups"),
        ("GET", "/api/owners/{ownerId}/hydrotap-system-faults/major", "Fault dashboard"),
        ("GET", "/api/owners/{ownerId}/hydrotap-system-faults/minor", "Alert dashboard"),
        ("GET", "/api/owners/{ownerId}/hydrotaps-without-system-faults", "Nominal taps"),
    ],
    "Other": [
        ("GET", "/api/sleep-modes", "Available sleep mode options"),
        ("GET", "/api/countries", "Country list"),
        ("GET", "/api/timezones", "Timezone list"),
        ("GET", "/api/hydrotaps/{id}/notes", "Admin notes for a tap"),
        ("POST", "/api/hydrotaps/{id}/notes", "Add a note"),
    ],
}


def print_endpoints() -> None:
    """Print all known endpoints in a machine-readable format."""
    for category, endpoints in KNOWN_ENDPOINTS.items():
        print(f"\n## {category}")
        for method, path, description in endpoints:
            print(f"  {method:6s} {path:55s} {description}")


# ------------------------------------------------------------------ explorer


class ZipAssistExplorer:
    """Explores the ZipAssist CMMS API."""

    API_AUTH_LOGIN = "/api/auth/jwt/login"
    API_AUTH_REFRESH = "/api/auth/jwt/refresh"

    def __init__(
        self,
        base_url: str | None = None,
        email: str | None = None,
        password: str | None = None,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("ZIPASSIST_BASE_URL", "https://zipassist.zipindustries.com")
        ).rstrip("/")
        self.email = email or os.getenv("ZIPASSIST_EMAIL", "")
        self.password = password or os.getenv("ZIPASSIST_PASSWORD", "")
        self.session: aiohttp.ClientSession | None = None
        self._token: str | None = None
        self._user: dict | None = None

    async def __aenter__(self) -> "ZipAssistExplorer":
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args: object) -> None:
        if self.session:
            await self.session.close()

    # ------------------------------------------------------------------ auth

    async def authenticate(self) -> bool:
        """Login and get a JWT token."""
        if not self.email or not self.password:
            _LOGGER.error("No credentials — cannot authenticate")
            _LOGGER.error("Set ZIPASSIST_EMAIL and ZIPASSIST_PASSWORD in .env or pass --email/--password")
            return False

        credentials = base64.b64encode(
            f"{self.email}:{self.password}".encode()
        ).decode()
        url = f"{self.base_url}{self.API_AUTH_LOGIN}"

        _LOGGER.info("Authenticating to %s as %s", url, self.email)
        async with self.session.get(  # pyright: ignore[union-attr]
            url,
            headers={"Authorization": f"Basic {credentials}"},
        ) as resp:
            data = await resp.json()
            _LOGGER.info("Auth status: %s", resp.status)

            if resp.status == 200:
                data = await resp.json()
                inner = data.get("data", data)
                self._token = data.get("token")
                self._user = inner.get("user", data.get("user", {}))
                _LOGGER.info(
                    "Authenticated as %s (%s)",
                    self._user.get("name", "?"),
                    self._user.get("userType", "?"),
                )
                return True
            else:
                _LOGGER.error("Auth failed: %s", data)
                return False

    def _auth_headers(self) -> dict[str, str]:
        """Return Authorization header if we have a token."""
        if self._token:
            return {"Authorization": f"Bearer {self._token}"}
        return {}

    async def _get(self, path: str, label: str = "") -> dict | list | None:
        url = f"{self.base_url}{path}"
        tag = label or path
        _LOGGER.info("GET %s", url)
        async with self.session.get(  # pyright: ignore[union-attr]
            url, headers=self._auth_headers()
        ) as resp:
            ct = resp.content_type
            if resp.status == 200 and "json" in ct:
                data = await resp.json()
                self._summarise(tag, data)
                return data
            elif resp.status == 200 and "html" in ct:
                _LOGGER.warning("  -> 200 HTML (probably redirected to login)")
                return None
            else:
                text = await resp.text()
                _LOGGER.warning("  -> %s %s", resp.status, text[:200])
                return None

    @staticmethod
    def _summarise(label: str, data: object) -> None:
        """Print a one-line summary of API response data."""
        if isinstance(data, list):
            _LOGGER.info("  %s: %d items", label, len(data))
            if data:
                first = data[0]
                if isinstance(first, dict):
                    _LOGGER.info("    keys: %s", sorted(first.keys()))
        elif isinstance(data, dict):
            _LOGGER.info("  %s: keys=%s", label, sorted(data.keys()))
        else:
            _LOGGER.info("  %s: type=%s", label, type(data).__name__)

    # --------------------------------------------------------------- runners

    async def explore_auth(self) -> None:
        """Explore auth-related endpoints."""
        _LOGGER.info("=== Auth ===")
        ok = await self.authenticate()
        if not ok:
            return
        await self._get(self.API_AUTH_REFRESH, "refresh")

    async def explore_hydrotaps(self) -> None:
        """Explore hydrotap-related endpoints."""
        _LOGGER.info("=== Hydrotaps ===")
        if not self._token:
            _LOGGER.warning("Not authenticated — skipping")
            return

        user_type = (self._user or {}).get("userType", "")
        data: dict | list | None = None

        if user_type == "owner":
            uid = (self._user or {}).get("owner", {}).get("ownerId", "")
            if uid:
                data = await self._get(
                    f"/api/owners/{uid}/hydrotaps", "hydrotaps"
                )
        elif user_type == "admin":
            data = await self._get("/api/hydrotaps", "hydrotaps")

        hydrotap_ids: list[str] = []
        if isinstance(data, list) and data:
            hydrotap_ids = [
                str(h.get("hydrotapId", "")) for h in data if isinstance(h, dict)
            ]
            _LOGGER.info("  Found %d hydrotap(s)", len(hydrotap_ids))

        for hid in hydrotap_ids[:2]:
            _LOGGER.info("--- Hydrotap %s ---", hid)
            await self._get(f"/api/hydrotaps/{hid}", "detail")
            await self._get(f"/api/hydrotaps/{hid}/settings", "settings")
            await self._get(
                f"/api/hydrotaps/{hid}/settings-options", "settings-options"
            )
            await self._get(
                f"/api/hydrotaps/{hid}/logs/general?limit=3", "status-logs"
            )
            await self._get(
                f"/api/hydrotaps/{hid}/logs/system-faults?currentOnly=true",
                "faults",
            )
            await self._get(
                f"/api/hydrotaps/{hid}/logs/filter-usage?limit=3", "filter-usage"
            )
            await self._get(
                f"/api/hydrotaps/{hid}/logs/dispense-events?limit=3",
                "dispense-events",
            )
            await self._get(
                f"/api/hydrotaps/{hid}/logs/daily-usage?limit=1", "daily-usage"
            )
            await self._get(f"/api/hydrotaps/{hid}/timezone", "timezone")
            await self._get(f"/api/hydrotaps/{hid}/notes", "notes")

    async def explore_other(self) -> None:
        """Explore user/admin/owner endpoints."""
        _LOGGER.info("=== Other Endpoints ===")
        if not self._token:
            _LOGGER.warning("Not authenticated — skipping")
            return

        user_type = (self._user or {}).get("userType", "")

        await self._get("/api/hydrotap-search-options", "search-options")
        await self._get("/api/countries", "countries")
        await self._get("/api/timezones", "timezones")
        await self._get("/api/system-faults", "system-faults")
        await self._get("/api/system-events", "system-events")
        await self._get("/api/sleep-modes", "sleep-modes")

        if user_type == "admin":
            await self._get("/api/admins", "admins")
        elif user_type == "owner":
            uid = (self._user or {}).get("owner", {}).get("ownerId", "")
            if uid:
                await self._get(f"/api/owners/{uid}", "owner-profile")
                await self._get(f"/api/owners/{uid}/hydrotaps", "owner-hydrotaps")
                await self._get(
                    f"/api/owners/{uid}/hydrotap-groups", "owner-groups"
                )
                await self._get(
                    f"/api/owners/{uid}/facility-managers",
                    "owner-facility-managers",
                )
                await self._get(
                    f"/api/owners/{uid}/alert-recipients", "alert-recipients"
                )
        elif user_type == "facilityManager":
            uid = (
                (self._user or {})
                .get("facilityManager", {})
                .get("facilityManagerId", "")
            )
            if uid:
                await self._get(f"/api/facility-managers/{uid}", "fm-profile")

    async def run(self) -> None:
        """Run the full exploration."""
        _LOGGER.info("ZipAssist CMMS API exploration")
        _LOGGER.info("Base URL: %s", self.base_url)

        await self.explore_auth()
        await self.explore_hydrotaps()
        await self.explore_other()

        _LOGGER.info("Exploration complete!")


# ------------------------------------------------------------------ main


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Explore the ZipAssist CMMS API.",
    )
    parser.add_argument(
        "--base-url",
        help="Override the API base URL (default: from ZIPASSIST_BASE_URL env var)",
    )
    parser.add_argument(
        "--email",
        help="Override the email (default: from ZIPASSIST_EMAIL env var)",
    )
    parser.add_argument(
        "--password",
        help="Override the password (default: from ZIPASSIST_PASSWORD env var)",
    )
    parser.add_argument(
        "--endpoints-only",
        action="store_true",
        help="Print the known endpoint list and exit (no network calls)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress non-error log output",
    )
    return parser


async def main() -> None:
    """Run the explorer."""
    parser = build_parser()
    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    if args.endpoints_only:
        print_endpoints()
        return

    async with ZipAssistExplorer(
        base_url=args.base_url,
        email=args.email,
        password=args.password,
    ) as explorer:
        await explorer.run()


if __name__ == "__main__":
    asyncio.run(main())