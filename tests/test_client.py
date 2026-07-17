"""Tests for the ZipAssist client."""

from __future__ import annotations

from custom_components.zipassist.client import ZipAssistClient


def test_client_initialization() -> None:
    """Test that the client initializes correctly."""
    client = ZipAssistClient(
        email="test@example.com",
        password="test_password",
    )
    assert client._email == "test@example.com"
    assert client._password == "test_password"
    assert client._base_url == "https://zipassist.zipindustries.com"
    assert client._token is None


def test_client_custom_base_url() -> None:
    """Test custom base URL stripping trailing slash."""
    client = ZipAssistClient(
        email="a@b.com",
        password="pw",
        base_url="https://example.com/",
    )
    assert client._base_url == "https://example.com"


def test_auth_headers_no_token() -> None:
    """Test auth headers return empty when no token."""
    client = ZipAssistClient(email="a@b.com", password="pw")
    assert client._auth_headers == {}