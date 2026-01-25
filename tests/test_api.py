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


@pytest.mark.asyncio
async def test_denormalize_posts():
    """denormalize_posts should join normalized data."""
    api = FreeFeedAPI("test-token")
    api.current_user = User(
        id="me-123",
        username="me",
        screen_name="Me",
        type="user",
    )

    normalized_data = {
        "posts": [
            {
                "id": "post-1",
                "body": "Hello world",
                "createdBy": "user-1",
                "createdAt": "1706097600000",
                "updatedAt": "1706097600000",
                "comments": ["comment-1"],
                "likes": ["user-2"],
                "postedTo": ["feed-1"],
                "omittedComments": 0,
                "omittedLikes": 0,
            }
        ],
        "comments": [
            {
                "id": "comment-1",
                "body": "Nice post!",
                "createdBy": "user-2",
                "createdAt": "1706097700000",
                "likes": 3,
            }
        ],
        "users": [
            {"id": "user-1", "username": "alice", "screenName": "Alice", "type": "user"},
            {"id": "user-2", "username": "bob", "screenName": "Bob", "type": "user"},
            {"id": "feed-1", "username": "news", "screenName": "News", "type": "group"},
        ],
    }

    posts = api._denormalize_posts(normalized_data)

    assert len(posts) == 1
    post = posts[0]
    assert post.id == "post-1"
    assert post.body == "Hello world"
    assert post.author.username == "alice"
    assert len(post.comments) == 1
    assert post.comments[0].body == "Nice post!"
    assert post.comments[0].author.username == "bob"
    assert len(post.groups) == 1
    assert post.groups[0].username == "news"


@pytest.mark.asyncio
async def test_get_home_feed():
    """get_home_feed should return list of posts."""
    api = FreeFeedAPI("test-token")
    api.current_user = User(id="me", username="me", screen_name="Me", type="user")

    mock_response = {
        "posts": [
            {
                "id": "p1",
                "body": "Test post",
                "createdBy": "u1",
                "createdAt": "1706097600000",
                "updatedAt": "1706097600000",
                "comments": [],
                "likes": [],
                "postedTo": [],
                "omittedComments": 0,
                "omittedLikes": 0,
            }
        ],
        "comments": [],
        "users": [
            {"id": "u1", "username": "alice", "screenName": "Alice", "type": "user"},
        ],
    }

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        posts = await api.get_home_feed()

        assert len(posts) == 1
        assert posts[0].body == "Test post"
        mock_client.get.assert_called_once_with(
            "/v2/timelines/home", params={"offset": 0, "limit": 30}
        )
