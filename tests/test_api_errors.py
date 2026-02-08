"""Tests for API error handling."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from freefood.api import FreeFeedAPI
from freefood.errors import ApiError, AuthError, NetworkError


@pytest.mark.asyncio
async def test_network_error_wrapping():
    """NetworkError should be raised on connection issues."""
    api = FreeFeedAPI("token")

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(
            side_effect=httpx.NetworkError("Connection failed")
        )
        mock_get_client.return_value = mock_client

        with pytest.raises(NetworkError, match="Network error"):
            # Trigger a request (e.g., validate_token calls _request)
            await api.validate_token()


@pytest.mark.asyncio
async def test_api_error_wrapping():
    """ApiError should be raised on 4xx/5xx responses."""
    api = FreeFeedAPI("token")

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        # Mock raise_for_status to raise HTTPStatusError
        error = httpx.HTTPStatusError(
            "Internal Server Error", request=MagicMock(), response=mock_response
        )
        mock_response.raise_for_status.side_effect = error

        mock_client.request = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        with pytest.raises(ApiError, match="API error"):
            await api.validate_token()


@pytest.mark.asyncio
async def test_auth_error_on_401():
    """AuthError should be raised on 401 responses."""
    api = FreeFeedAPI("token")

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        error = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )
        mock_response.raise_for_status.side_effect = error
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        with pytest.raises(AuthError, match="Auth error"):
            await api.validate_token()


@pytest.mark.asyncio
async def test_request_error_wrapping():
    """NetworkError should be raised on generic request errors."""
    api = FreeFeedAPI("token")

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(side_effect=httpx.ReadTimeout("Timeout"))
        mock_get_client.return_value = mock_client

        with pytest.raises(NetworkError, match="Request error"):
            await api.validate_token()
