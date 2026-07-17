"""Tests for the ZipAssist client."""

from __future__ import annotations

import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import the client without Home Assistant dependencies
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "custom_components", "zipassist"
    ),
)

from client import ZipAssistClient, _jwt_expiry  # noqa: E402

# ------------------------------------------------------------------ helpers


def _b64_encode(s: str) -> str:
    """Base64url encode without padding."""
    import base64

    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")


def _make_mock_response(status=200, content_type="application/json", json_data=None):
    """Create a mock response that works with async context manager."""
    resp = MagicMock()
    resp.status = status
    resp.content_type = content_type
    resp.json = AsyncMock(return_value=json_data)
    # Make it an async context manager
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=None)
    return resp


def _make_mock_session(get_response=None, patch_response=None):
    """Create a mock aiohttp session."""
    session = MagicMock()
    if get_response:
        session.get = MagicMock(return_value=get_response)
    if patch_response:
        session.patch = MagicMock(return_value=patch_response)
    return session


# ------------------------------------------------------------------ JWT helpers


class TestJwtExpiry:
    """Tests for _jwt_expiry."""

    def test_valid_token(self) -> None:
        """Test extracting exp from a valid JWT."""
        header = _b64_encode(json.dumps({"alg": "HS256", "typ": "JWT"}))
        payload = _b64_encode(json.dumps({"exp": 1234567890, "sub": "user"}))
        token = f"{header}.{payload}.sig"
        assert _jwt_expiry(token) == 1234567890.0

    def test_no_exp_claim(self) -> None:
        """Test JWT without exp claim returns 0."""
        header = _b64_encode(json.dumps({"alg": "HS256"}))
        payload = _b64_encode(json.dumps({"sub": "user"}))
        token = f"{header}.{payload}.sig"
        assert _jwt_expiry(token) == 0.0

    def test_malformed_token(self) -> None:
        """Test malformed token returns 0."""
        assert _jwt_expiry("not-a-jwt") == 0.0
        assert _jwt_expiry("") == 0.0

    def test_invalid_base64(self) -> None:
        """Test invalid base64 in payload returns 0."""
        assert _jwt_expiry("a.!!!.c") == 0.0


# ------------------------------------------------------------------ client init


class TestClientInit:
    """Tests for client initialization."""

    def test_default_values(self) -> None:
        """Test client initializes with correct defaults."""
        client = ZipAssistClient(email="test@example.com", password="pw")
        assert client._email == "test@example.com"
        assert client._password == "pw"
        assert client._base_url == "https://zipassist.zipindustries.com"
        assert client._token is None
        assert client._token_expiry == 0

    def test_custom_base_url(self) -> None:
        """Test custom base URL with trailing slash stripped."""
        client = ZipAssistClient(
            email="a@b.com", password="pw", base_url="https://example.com/"
        )
        assert client._base_url == "https://example.com"

    def test_custom_base_url_no_slash(self) -> None:
        """Test custom base URL without trailing slash."""
        client = ZipAssistClient(
            email="a@b.com", password="pw", base_url="https://example.com"
        )
        assert client._base_url == "https://example.com"

    def test_auth_headers_no_token(self) -> None:
        """Test auth headers return empty when no token."""
        client = ZipAssistClient(email="a@b.com", password="pw")
        assert client._auth_headers == {}

    def test_auth_headers_with_token(self) -> None:
        """Test auth headers include Bearer token."""
        client = ZipAssistClient(email="a@b.com", password="pw")
        client._token = "test-token"
        assert client._auth_headers == {"Authorization": "Bearer test-token"}

    def test_token_expiring_soon_no_token(self) -> None:
        """Test token_expiring_soon returns True when no token."""
        client = ZipAssistClient(email="a@b.com", password="pw")
        assert client._token_expiring_soon is True

    def test_token_expiring_soon_expired(self) -> None:
        """Test token_expiring_soon returns True when token is expired."""
        import time

        client = ZipAssistClient(email="a@b.com", password="pw")
        client._token = "token"
        client._token_expiry = time.time() - 100
        assert client._token_expiring_soon is True

    def test_token_expiring_soon_valid(self) -> None:
        """Test token_expiring_soon returns False when token is fresh."""
        import time

        client = ZipAssistClient(email="a@b.com", password="pw")
        client._token = "token"
        client._token_expiry = time.time() + 3600
        assert client._token_expiring_soon is False


# ------------------------------------------------------------------ auth


class TestAuth:
    """Tests for authentication."""

    @pytest.mark.asyncio
    async def test_authenticate_success(self) -> None:
        """Test successful authentication."""
        # Create a JWT with a valid exp claim
        header = _b64_encode(json.dumps({"alg": "HS256", "typ": "JWT"}))
        payload = _b64_encode(json.dumps({"exp": 9999999999, "sub": "user"}))
        jwt_token = f"{header}.{payload}.sig"

        resp = _make_mock_response(
            json_data={"token": jwt_token, "user": {"name": "Test"}}
        )
        session = _make_mock_session(get_response=resp)

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._session = session

        result = await client.authenticate()
        assert result is True
        assert client._token == jwt_token
        assert client._token_expiry == 9999999999.0

    @pytest.mark.asyncio
    async def test_authenticate_failure(self) -> None:
        """Test failed authentication."""
        resp = _make_mock_response(status=401)
        session = _make_mock_session(get_response=resp)

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._session = session

        result = await client.authenticate()
        assert result is False

    @pytest.mark.asyncio
    async def test_authenticate_no_token_in_response(self) -> None:
        """Test auth response without token."""
        resp = _make_mock_response(json_data={"user": {"name": "Test"}})
        session = _make_mock_session(get_response=resp)

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._session = session

        result = await client.authenticate()
        assert result is False

    @pytest.mark.asyncio
    async def test_authenticate_extracts_owner_id(self) -> None:
        """Test auth extracts ownerId from response."""
        header = _b64_encode(json.dumps({"alg": "HS256", "typ": "JWT"}))
        payload = _b64_encode(json.dumps({"exp": 9999999999, "sub": "user"}))
        jwt_token = f"{header}.{payload}.sig"

        resp = _make_mock_response(
            json_data={
                "token": jwt_token,
                "user": {
                    "name": "Owner User",
                    "userType": "owner",
                    "owner": {"ownerId": "owner-uuid-123"},
                },
            }
        )
        session = _make_mock_session(get_response=resp)

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._session = session

        result = await client.authenticate()
        assert result is True
        assert client._user.get("userType") == "owner"
        assert client._owner_id == "owner-uuid-123"

    @pytest.mark.asyncio
    async def test_authenticate_admin_user(self) -> None:
        """Test auth for admin user (no ownerId)."""
        header = _b64_encode(json.dumps({"alg": "HS256", "typ": "JWT"}))
        payload = _b64_encode(json.dumps({"exp": 9999999999, "sub": "user"}))
        jwt_token = f"{header}.{payload}.sig"

        resp = _make_mock_response(
            json_data={
                "token": jwt_token,
                "user": {"name": "Admin", "userType": "admin"},
            }
        )
        session = _make_mock_session(get_response=resp)

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._session = session

        result = await client.authenticate()
        assert result is True
        assert client._user.get("userType") == "admin"
        assert client._owner_id is None

    @pytest.mark.asyncio
    async def test_authenticate_nested_data_user(self) -> None:
        """Test auth with user nested under data.user."""
        header = _b64_encode(json.dumps({"alg": "HS256", "typ": "JWT"}))
        payload = _b64_encode(json.dumps({"exp": 9999999999, "sub": "user"}))
        jwt_token = f"{header}.{payload}.sig"

        resp = _make_mock_response(
            json_data={
                "token": jwt_token,
                "data": {
                    "user": {
                        "name": "Nested User",
                        "userType": "owner",
                        "owner": {"ownerId": "nested-owner-id"},
                    }
                },
            }
        )
        session = _make_mock_session(get_response=resp)

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._session = session

        result = await client.authenticate()
        assert result is True
        assert client._owner_id == "nested-owner-id"

    @pytest.mark.asyncio
    async def test_authenticate_flat_owner_id(self) -> None:
        """Test auth with ownerId directly on user object."""
        header = _b64_encode(json.dumps({"alg": "HS256", "typ": "JWT"}))
        payload = _b64_encode(json.dumps({"exp": 9999999999, "sub": "user"}))
        jwt_token = f"{header}.{payload}.sig"

        resp = _make_mock_response(
            json_data={
                "token": jwt_token,
                "user": {
                    "name": "Flat User",
                    "userType": "owner",
                    "ownerId": "flat-owner-id",
                },
            }
        )
        session = _make_mock_session(get_response=resp)

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._session = session

        result = await client.authenticate()
        assert result is True
        assert client._owner_id == "flat-owner-id"

    @pytest.mark.asyncio
    async def test_refresh_token_success(self) -> None:
        """Test successful token refresh."""
        resp = _make_mock_response(json_data={"token": "new-jwt"})
        session = _make_mock_session(get_response=resp)

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._token = "old-jwt"
        client._session = session

        result = await client.refresh_token()
        assert result is True
        assert client._token == "new-jwt"

    @pytest.mark.asyncio
    async def test_refresh_token_no_token(self) -> None:
        """Test refresh when no token exists."""
        client = ZipAssistClient(email="test@example.com", password="pw")
        result = await client.refresh_token()
        assert result is False

    @pytest.mark.asyncio
    async def test_refresh_token_failure(self) -> None:
        """Test failed token refresh."""
        resp = _make_mock_response(status=401)
        session = _make_mock_session(get_response=resp)

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._token = "old-jwt"
        client._session = session

        result = await client.refresh_token()
        assert result is False


# ------------------------------------------------------------------ API calls


class TestApiCalls:
    """Tests for API methods."""

    def _make_client(self, get_json=None, patch_status=200):
        """Create a client with a mocked session."""
        resp = _make_mock_response(json_data=get_json)
        session = _make_mock_session(get_response=resp)
        if patch_status is not None:
            patch_resp = _make_mock_response(status=patch_status)
            session.patch = MagicMock(return_value=patch_resp)

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._token = "jwt"
        client._token_expiry = 9999999999
        client._session = session
        return client

    @pytest.mark.asyncio
    async def test_get_hydrotaps(self) -> None:
        """Test get_hydrotaps returns list."""
        client = self._make_client(get_json=[{"hydrotapId": "abc"}])
        result = await client.get_hydrotaps()
        assert result == [{"hydrotapId": "abc"}]

    @pytest.mark.asyncio
    async def test_get_hydrotaps_non_list(self) -> None:
        """Test get_hydrotaps returns empty list for non-list response."""
        client = self._make_client(get_json={"error": "not found"})
        result = await client.get_hydrotaps()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_settings(self) -> None:
        """Test get_settings returns dict."""
        client = self._make_client(get_json={"boiling": {"temp": 98}})
        result = await client.get_settings("tap-1")
        assert result == {"boiling": {"temp": 98}}

    @pytest.mark.asyncio
    async def test_get_settings_options(self) -> None:
        """Test get_settings_options returns dict."""
        client = self._make_client(get_json={"water": {}})
        result = await client.get_settings_options("tap-1")
        assert result == {"water": {}}

    @pytest.mark.asyncio
    async def test_get_current_faults(self) -> None:
        """Test get_current_faults returns list."""
        client = self._make_client(
            get_json=[{"faultCode": "F01", "description": "Leak"}]
        )
        result = await client.get_current_faults("tap-1")
        assert result == [{"faultCode": "F01", "description": "Leak"}]

    @pytest.mark.asyncio
    async def test_get_current_faults_non_list(self) -> None:
        """Test get_current_faults returns empty list for non-list."""
        client = self._make_client(get_json={"error": "x"})
        result = await client.get_current_faults("tap-1")
        assert result == []

    @pytest.mark.asyncio
    async def test_update_settings_success(self) -> None:
        """Test update_settings returns True on success."""
        client = self._make_client(patch_status=200)
        result = await client.update_settings("tap-1", {"boiling": {"temp": 95}})
        assert result is True

    @pytest.mark.asyncio
    async def test_update_settings_failure(self) -> None:
        """Test update_settings returns False on failure."""
        client = self._make_client(patch_status=400)
        result = await client.update_settings("tap-1", {"bad": "data"})
        assert result is False

    @pytest.mark.asyncio
    async def test_get_latest_log(self) -> None:
        """Test get_latest_log returns first item."""
        client = self._make_client(
            get_json=[{"hydrotapLogId": "log-1", "energyKwhTotal": 100}]
        )
        result = await client.get_latest_log("tap-1")
        assert result == {"hydrotapLogId": "log-1", "energyKwhTotal": 100}

    @pytest.mark.asyncio
    async def test_get_latest_log_empty(self) -> None:
        """Test get_latest_log returns None for empty list."""
        client = self._make_client(get_json=[])
        result = await client.get_latest_log("tap-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_hydrotap_detail(self) -> None:
        """Test get_hydrotap returns dict."""
        client = self._make_client(
            get_json={"hydrotapId": "tap-1", "moduleName": "BC 100"}
        )
        result = await client.get_hydrotap("tap-1")
        assert result == {"hydrotapId": "tap-1", "moduleName": "BC 100"}

    @pytest.mark.asyncio
    async def test_get_status_logs(self) -> None:
        """Test get_status_logs returns list."""
        client = self._make_client(get_json=[{"hydrotapLogId": "log-1"}])
        result = await client.get_status_logs("tap-1")
        assert result == [{"hydrotapLogId": "log-1"}]

    @pytest.mark.asyncio
    async def test_get_hydrotaps_owner_route(self) -> None:
        """Test get_hydrotaps uses owner-specific endpoint."""
        client = self._make_client(get_json=[{"hydrotapId": "owner-tap"}])
        client._user = {"userType": "owner"}
        client._owner_id = "owner-123"

        result = await client.get_hydrotaps()
        assert result == [{"hydrotapId": "owner-tap"}]
        # Verify it called the owner endpoint
        call_url = client._session.get.call_args[0][0]
        assert "/api/owners/owner-123/hydrotaps" in call_url

    @pytest.mark.asyncio
    async def test_get_hydrotaps_owner_fallback(self) -> None:
        """Test get_hydrotaps falls back to admin endpoint."""
        # First response (owner endpoint) returns non-list
        resp_owner = _make_mock_response(json_data={"error": "forbidden"})
        # Second response (admin endpoint) returns list
        resp_admin = _make_mock_response(json_data=[{"hydrotapId": "admin-tap"}])

        session = _make_mock_session(get_response=resp_owner)
        session.get = MagicMock(side_effect=[resp_owner, resp_admin])

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._token = "jwt"
        client._token_expiry = 9999999999
        client._session = session
        client._user = {"userType": "owner"}
        client._owner_id = "owner-123"

        result = await client.get_hydrotaps()
        assert result == [{"hydrotapId": "admin-tap"}]
        assert session.get.call_count == 2

    @pytest.mark.asyncio
    async def test_get_hydrotaps_admin_route(self) -> None:
        """Test get_hydrotaps uses admin endpoint for admin users."""
        client = self._make_client(get_json=[{"hydrotapId": "admin-tap"}])
        client._user = {"userType": "admin"}

        result = await client.get_hydrotaps()
        assert result == [{"hydrotapId": "admin-tap"}]
        call_url = client._session.get.call_args[0][0]
        assert "/api/hydrotaps" in call_url

    @pytest.mark.asyncio
    async def test_get_hydrotaps_no_user_type(self) -> None:
        """Test get_hydrotaps uses admin endpoint when no user type."""
        client = self._make_client(get_json=[{"hydrotapId": "tap"}])
        # _user is empty dict by default

        result = await client.get_hydrotaps()
        assert result == [{"hydrotapId": "tap"}]
        call_url = client._session.get.call_args[0][0]
        assert "/api/hydrotaps" in call_url


# ------------------------------------------------------------------ lifecycle


class TestLifecycle:
    """Tests for client lifecycle."""

    @pytest.mark.asyncio
    async def test_close_own_session(self) -> None:
        """Test close closes own session."""
        mock_session = MagicMock()
        mock_session.close = AsyncMock()

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._session = mock_session
        client._own_session = True

        await client.close()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_external_session(self) -> None:
        """Test close does not close external session."""
        mock_session = MagicMock()
        mock_session.close = AsyncMock()

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._session = mock_session
        client._own_session = False

        await client.close()
        mock_session.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_close_no_session(self) -> None:
        """Test close with no session is safe."""
        client = ZipAssistClient(email="test@example.com", password="pw")
        await client.close()  # should not raise


# ------------------------------------------------------------------ 401 retry


class TestRetryOn401:
    """Tests for 401 retry logic."""

    @pytest.mark.asyncio
    async def test_get_retries_on_401(self) -> None:
        """Test _get retries on 401."""
        resp_401 = _make_mock_response(status=401)
        resp_200 = _make_mock_response(json_data={"data": "ok"})
        session = _make_mock_session(get_response=resp_401)
        # Override get to return 401 then 200
        session.get = MagicMock(side_effect=[resp_401, resp_200])

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._token = "jwt"
        client._token_expiry = 9999999999
        client._session = session
        client.authenticate = AsyncMock(return_value=True)

        result = await client._get("/api/test")
        assert result == {"data": "ok"}
        assert session.get.call_count == 2

    @pytest.mark.asyncio
    async def test_get_401_retry_fails(self) -> None:
        """Test _get returns None when retry also fails."""
        resp_401 = _make_mock_response(status=401)
        session = _make_mock_session(get_response=resp_401)

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._token = "jwt"
        client._token_expiry = 9999999999
        client._session = session
        client.authenticate = AsyncMock(return_value=False)

        result = await client._get("/api/test")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_non_200_non_401(self) -> None:
        """Test _get returns None for non-200, non-401 status."""
        resp = _make_mock_response(status=500)
        session = _make_mock_session(get_response=resp)

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._token = "jwt"
        client._token_expiry = 9999999999
        client._session = session

        result = await client._get("/api/test")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_non_json_content_type(self) -> None:
        """Test _get returns None for non-JSON content type."""
        resp = _make_mock_response(status=200, content_type="text/html")
        session = _make_mock_session(get_response=resp)

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._token = "jwt"
        client._token_expiry = 9999999999
        client._session = session

        result = await client._get("/api/test")
        assert result is None


# ------------------------------------------------------------------ ensure fresh token


class TestEnsureFreshToken:
    """Tests for _ensure_fresh_token."""

    @pytest.mark.asyncio
    async def test_no_refresh_needed(self) -> None:
        """Test no refresh when token is fresh."""
        import time

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._token = "jwt"
        client._token_expiry = time.time() + 3600

        client.refresh_token = AsyncMock()
        client.authenticate = AsyncMock()

        await client._ensure_fresh_token()
        client.refresh_token.assert_not_called()
        client.authenticate.assert_not_called()

    @pytest.mark.asyncio
    async def test_refresh_succeeds(self) -> None:
        """Test refresh is called when token is near expiry."""
        import time

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._token = "jwt"
        client._token_expiry = time.time() + 60

        client.refresh_token = AsyncMock(return_value=True)
        client.authenticate = AsyncMock()

        await client._ensure_fresh_token()
        client.refresh_token.assert_called_once()
        client.authenticate.assert_not_called()

    @pytest.mark.asyncio
    async def test_refresh_fails_falls_back_to_auth(self) -> None:
        """Test full re-auth when refresh fails."""
        import time

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._token = "jwt"
        client._token_expiry = time.time() + 60

        client.refresh_token = AsyncMock(return_value=False)
        client.authenticate = AsyncMock(return_value=True)

        await client._ensure_fresh_token()
        client.refresh_token.assert_called_once()
        client.authenticate.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_token_full_auth(self) -> None:
        """Test full auth when no token exists."""
        client = ZipAssistClient(email="test@example.com", password="pw")
        client._token = None

        client.refresh_token = AsyncMock()
        client.authenticate = AsyncMock(return_value=True)

        await client._ensure_fresh_token()
        client.refresh_token.assert_not_called()
        client.authenticate.assert_called_once()


# ------------------------------------------------------------------ clear fault


class TestClearFault:
    """Tests for clear_fault."""

    @pytest.mark.asyncio
    async def test_clear_fault_success(self) -> None:
        """Test clearing a fault successfully."""
        resp = _make_mock_response(status=200)
        session = _make_mock_session(patch_response=resp)

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._token = "jwt"
        client._token_expiry = 9999999999
        client._session = session

        result = await client.clear_fault(
            "tap-1", "fault-1", "2026-07-18T00:00:00+0000"
        )
        assert result is True
        session.patch.assert_called_once()
        call_args = session.patch.call_args
        assert "tap-1" in call_args[0][0]
        assert "fault-1" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_clear_fault_failure(self) -> None:
        """Test clearing a fault fails."""
        resp = _make_mock_response(status=400)
        session = _make_mock_session(patch_response=resp)

        client = ZipAssistClient(email="test@example.com", password="pw")
        client._token = "jwt"
        client._token_expiry = 9999999999
        client._session = session

        result = await client.clear_fault(
            "tap-1", "fault-1", "2026-07-18T00:00:00+0000"
        )
        assert result is False