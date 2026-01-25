"""Tests for FreeFeed API client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from freefood.api import FreeFeedAPI
from freefood.models import User


def test_api_client_initialization():
    """API client should initialize with token."""
    api = FreeFeedAPI("test-token")
    assert api.token == "test-token"
    assert api.current_user is None


def test_api_client_base_url():
    """API client should have correct base URL."""
    api = FreeFeedAPI("test-token")
    assert api.BASE_URL == "https://freefeed.net"


@pytest.mark.asyncio
async def test_validate_token_success():
    """validate_token should return User on success."""
    api = FreeFeedAPI("test-token")

    mock_response = {
        "users": {
            "id": "user-123",
            "username": "testuser",
            "screenName": "Test User",
            "type": "user",
        }
    }

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        user = await api.validate_token()

        assert user.id == "user-123"
        assert user.username == "testuser"
        assert user.screen_name == "Test User"
        assert api.current_user == user
        mock_client.get.assert_called_once_with("/v2/users/whoami")
