"""Tests for FreeFeed API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from freefood.api import FreeFeedAPI
from freefood.models import User


@pytest.fixture
def mock_client():
    """Create a mock HTTP client."""
    client = AsyncMock()
    # Ensure request returns a mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_response.raise_for_status = MagicMock()
    client.request = AsyncMock(return_value=mock_response)
    return client


@pytest.fixture
def api():
    """Create an API client instance."""
    return FreeFeedAPI("test-token")


def test_api_client_initialization():
    """API client should initialize with token."""
    api = FreeFeedAPI("test-token")
    assert api.token == "test-token"
    assert api.current_user is None


@pytest.mark.asyncio
async def test_validate_token_success(api, mock_client):
    """validate_token should call whoami."""
    mock_response = {
        "users": {
            "id": "user-123",
            "username": "testuser",
            "screenName": "Test User",
            "type": "user",
        }
    }
    mock_client.request.return_value.json.return_value = mock_response

    with patch.object(api, "_get_client", return_value=mock_client):
        user = await api.validate_token()

    assert user.id == "user-123"
    assert api.current_user == user
    mock_client.request.assert_called_once_with("GET", "/v4/users/whoami")


@pytest.mark.asyncio
async def test_get_home_feed(api, mock_client):
    """get_home_feed should call home timeline."""
    mock_response = {"posts": [], "users": []}
    mock_client.request.return_value.json.return_value = mock_response

    with patch.object(api, "_get_client", return_value=mock_client):
        await api.get_home_feed(offset=10, limit=20)

    mock_client.request.assert_called_once_with(
        "GET", "/v4/timelines/home", params={"offset": 10, "limit": 20}
    )


@pytest.mark.asyncio
async def test_get_user_feed(api, mock_client):
    """get_user_feed should call user timeline."""
    mock_response = {"posts": [], "users": []}
    mock_client.request.return_value.json.return_value = mock_response

    with patch.object(api, "_get_client", return_value=mock_client):
        await api.get_user_feed("alice")

    mock_client.request.assert_called_once_with(
        "GET", "/v4/timelines/alice", params={"offset": 0, "limit": 30}
    )


@pytest.mark.asyncio
async def test_search(api, mock_client):
    """search should call search endpoint."""
    mock_response = {"posts": [], "users": []}
    mock_client.request.return_value.json.return_value = mock_response

    with patch.object(api, "_get_client", return_value=mock_client):
        await api.search("query")

    mock_client.request.assert_called_once_with(
        "GET", "/v4/search", params={"q": "query", "offset": 0, "limit": 30}
    )


@pytest.mark.asyncio
async def test_get_post(api, mock_client):
    """get_post should call post endpoint."""
    # Note: get_post expects a list of posts in response usually, but handles empty
    mock_response = {"posts": [], "users": []}
    mock_client.request.return_value.json.return_value = mock_response

    with patch.object(api, "_get_client", return_value=mock_client):
        await api.get_post("p1")

    mock_client.request.assert_called_once_with(
        "GET", "/v4/posts/p1", params={"maxComments": "all", "maxLikes": "all"}
    )


@pytest.mark.asyncio
async def test_create_post(api, mock_client):
    """create_post should POST to posts endpoint."""
    mock_response = {
        "posts": {
            "id": "p1",
            "body": "Body",
            "createdBy": "u1",
            "createdAt": "1234567890000",
            "updatedAt": "1234567890000",
            "likes": [],
            "postedTo": [],
            "comments": [],
        },
        "users": [{"id": "u1", "username": "me"}],
    }
    mock_client.request.return_value.json.return_value = mock_response

    with patch.object(api, "_get_client", return_value=mock_client):
        await api.create_post("Body", ["feed"])

    mock_client.request.assert_called_once_with(
        "POST",
        "/v4/posts",
        json={"post": {"body": "Body"}, "meta": {"feeds": ["feed"]}},
    )


@pytest.mark.asyncio
async def test_like_post(api, mock_client):
    """like_post should POST to like endpoint."""
    with patch.object(api, "_get_client", return_value=mock_client):
        await api.like_post("p1")

    mock_client.request.assert_called_once_with("POST", "/v4/posts/p1/like")


@pytest.mark.asyncio
async def test_unlike_post(api, mock_client):
    """unlike_post should POST to unlike endpoint."""
    with patch.object(api, "_get_client", return_value=mock_client):
        await api.unlike_post("p1")

    mock_client.request.assert_called_once_with("POST", "/v4/posts/p1/unlike")


@pytest.mark.asyncio
async def test_create_comment(api, mock_client):
    """create_comment should POST to comments endpoint."""
    mock_response = {
        "comments": {
            "id": "c1",
            "body": "B",
            "createdBy": "me",
            "createdAt": "1234567890000",
            "likes": 0,
        },
        "users": [{"id": "me", "username": "me"}],
    }
    mock_client.request.return_value.json.return_value = mock_response
    
    # Mock current user for response parsing
    api.current_user = User(id="me", username="me", screen_name="Me", type="user")

    with patch.object(api, "_get_client", return_value=mock_client):
        await api.create_comment("p1", "Comment")

    mock_client.request.assert_called_once_with(
        "POST",
        "/v4/comments",
        json={"comment": {"body": "Comment", "postId": "p1"}},
    )


@pytest.mark.asyncio
async def test_get_notifications(api, mock_client):
    """get_notifications should call notifications endpoint."""
    mock_response = {"Notifications": [], "users": []}
    mock_client.request.return_value.json.return_value = mock_response

    with patch.object(api, "_get_client", return_value=mock_client):
        await api.get_notifications()

    mock_client.request.assert_called_once_with(
        "GET", "/v4/notifications", params={"offset": 0, "limit": 30}
    )


@pytest.mark.asyncio
async def test_get_unread_counts(api, mock_client):
    """get_unread_*_count calls should call whoami."""
    mock_response = {"unreadNotificationsNumber": 5, "unreadDirectsNumber": 2}
    mock_client.request.return_value.json.return_value = mock_response

    with patch.object(api, "_get_client", return_value=mock_client):
        n_count = await api.get_unread_notifications_count()
        d_count = await api.get_unread_directs_count()

    assert n_count == 5
    assert d_count == 2
    assert mock_client.request.call_count == 2
    mock_client.request.assert_called_with("GET", "/v4/users/whoami")
