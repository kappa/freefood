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
        mock_client.get.assert_called_once_with("/v4/users/whoami")


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
async def test_denormalize_posts_sets_direct_recipients():
    """denormalize_posts should map direct recipients from subscriptions."""
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
                "body": "Direct message",
                "createdBy": "user-1",
                "createdAt": "1706097600000",
                "updatedAt": "1706097600000",
                "comments": [],
                "likes": [],
                "postedTo": ["direct-1", "direct-2"],
                "omittedComments": 0,
                "omittedLikes": 0,
            }
        ],
        "users": [
            {"id": "user-1", "username": "alice", "screenName": "Alice", "type": "user"},
            {"id": "user-2", "username": "bob", "screenName": "Bob", "type": "user"},
        ],
        "subscriptions": [
            {"id": "direct-1", "name": "Directs", "user": "user-1"},
            {"id": "direct-2", "name": "Directs", "user": "user-2"},
        ],
    }

    posts = api._denormalize_posts(normalized_data)

    assert [u.username for u in posts[0].direct_recipients] == ["bob"]


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
            "/v4/timelines/home", params={"offset": 0, "limit": 30}
        )


@pytest.mark.asyncio
async def test_get_user_feed():
    """get_user_feed should return list of posts for a specific user."""
    api = FreeFeedAPI("test-token")
    api.current_user = User(id="me", username="me", screen_name="Me", type="user")

    mock_response = {
        "posts": [
            {
                "id": "p1",
                "body": "User post",
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

        posts = await api.get_user_feed("alice")

        assert len(posts) == 1
        assert posts[0].body == "User post"
        assert posts[0].author.username == "alice"
        mock_client.get.assert_called_once_with(
            "/v4/timelines/alice", params={"offset": 0, "limit": 30}
        )


@pytest.mark.asyncio
async def test_get_directs():
    """get_directs should return list of direct message posts."""
    api = FreeFeedAPI("test-token")
    api.current_user = User(id="me", username="me", screen_name="Me", type="user")

    mock_response = {
        "posts": [
            {
                "id": "dm1",
                "body": "Private message",
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
            {"id": "u1", "username": "bob", "screenName": "Bob", "type": "user"},
        ],
    }

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        posts = await api.get_directs()

        assert len(posts) == 1
        assert posts[0].body == "Private message"
        mock_client.get.assert_called_once_with(
            "/v4/timelines/filter/directs", params={"offset": 0, "limit": 30}
        )


@pytest.mark.asyncio
async def test_search():
    """search should return posts matching the query."""
    api = FreeFeedAPI("test-token")
    api.current_user = User(id="me", username="me", screen_name="Me", type="user")

    mock_response = {
        "posts": [
            {
                "id": "s1",
                "body": "Found post with keyword",
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
            {"id": "u1", "username": "charlie", "screenName": "Charlie", "type": "user"},
        ],
    }

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        posts = await api.search("keyword")

        assert len(posts) == 1
        assert posts[0].body == "Found post with keyword"
        mock_client.get.assert_called_once_with(
            "/v4/search", params={"q": "keyword", "offset": 0, "limit": 30}
        )


@pytest.mark.asyncio
async def test_get_post():
    """get_post should return a single post with all comments."""
    api = FreeFeedAPI("test-token")
    api.current_user = User(id="me", username="me", screen_name="Me", type="user")

    mock_response = {
        "posts": [
            {
                "id": "post-123",
                "body": "Single post",
                "createdBy": "u1",
                "createdAt": "1706097600000",
                "updatedAt": "1706097600000",
                "comments": ["c1"],
                "likes": [],
                "postedTo": [],
                "omittedComments": 0,
                "omittedLikes": 0,
            }
        ],
        "comments": [
            {
                "id": "c1",
                "body": "A comment",
                "createdBy": "u2",
                "createdAt": "1706097700000",
                "likes": 0,
            }
        ],
        "users": [
            {"id": "u1", "username": "dave", "screenName": "Dave", "type": "user"},
            {"id": "u2", "username": "eve", "screenName": "Eve", "type": "user"},
        ],
    }

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        post = await api.get_post("post-123")

        assert post is not None
        assert post.id == "post-123"
        assert post.body == "Single post"
        assert len(post.comments) == 1
        assert post.comments[0].body == "A comment"
        mock_client.get.assert_called_once_with(
            "/v4/posts/post-123", params={"maxComments": "all", "maxLikes": "all"}
        )


@pytest.mark.asyncio
async def test_get_post_single_object_response():
    """get_post should handle API response where posts is a single dict, not a list.

    The FreeFeed API returns posts as a dict (single object) for single-post endpoints,
    not as a list like timeline endpoints do.
    """
    api = FreeFeedAPI("test-token")
    api.current_user = User(id="me", username="me", screen_name="Me", type="user")

    # Real API response structure for single post - posts is a DICT not a list
    mock_response = {
        "posts": {
            "id": "post-456",
            "body": "Single post from real API",
            "createdBy": "u1",
            "createdAt": "1706097600000",
            "updatedAt": "1706097600000",
            "comments": ["c1", "c2"],
            "likes": ["u2"],
            "postedTo": ["feed-1"],
            "omittedComments": 0,
            "omittedLikes": 0,
        },
        "comments": [
            {
                "id": "c1",
                "body": "First comment",
                "createdBy": "u2",
                "createdAt": "1706097700000",
                "likes": 2,
            },
            {
                "id": "c2",
                "body": "Second comment",
                "createdBy": "u1",
                "createdAt": "1706097800000",
                "likes": 0,
            },
        ],
        "users": [
            {"id": "u1", "username": "alice", "screenName": "Alice", "type": "user"},
            {"id": "u2", "username": "bob", "screenName": "Bob", "type": "user"},
            {"id": "feed-1", "username": "news", "screenName": "News", "type": "group"},
        ],
    }

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        post = await api.get_post("post-456")

        assert post is not None
        assert post.id == "post-456"
        assert post.body == "Single post from real API"
        assert post.author.username == "alice"
        assert len(post.comments) == 2
        assert post.comments[0].body == "First comment"
        assert post.comments[1].body == "Second comment"
        assert len(post.groups) == 1
        assert post.groups[0].username == "news"


@pytest.mark.asyncio
async def test_get_post_not_found():
    """get_post should return None when no posts are in response."""
    api = FreeFeedAPI("test-token")
    api.current_user = User(id="me", username="me", screen_name="Me", type="user")

    mock_response = {
        "posts": [],
        "comments": [],
        "users": [],
    }

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        post = await api.get_post("nonexistent-id")

        assert post is None


@pytest.mark.asyncio
async def test_like_post():
    """like_post should POST to correct endpoint."""
    api = FreeFeedAPI("test-token")

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        await api.like_post("post-123")

        mock_client.post.assert_called_once_with("/v4/posts/post-123/like")


@pytest.mark.asyncio
async def test_unlike_post():
    """unlike_post should POST to correct endpoint."""
    api = FreeFeedAPI("test-token")

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        await api.unlike_post("post-123")

        mock_client.post.assert_called_once_with("/v4/posts/post-123/unlike")


@pytest.mark.asyncio
async def test_create_post():
    """create_post should POST with correct body."""
    api = FreeFeedAPI("test-token")
    api.current_user = User(id="me", username="me", screen_name="Me", type="user")

    mock_response = {
        "posts": [
            {
                "id": "new-post",
                "body": "Hello!",
                "createdBy": "me",
                "createdAt": "1706097600000",
                "updatedAt": "1706097600000",
                "comments": [],
                "likes": [],
                "postedTo": [],
                "omittedComments": 0,
                "omittedLikes": 0,
            }
        ],
        "users": [{"id": "me", "username": "me", "screenName": "Me", "type": "user"}],
        "comments": [],
    }

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        post = await api.create_post("Hello!", ["news"])

    assert post.body == "Hello!"
    mock_client.post.assert_called_once_with(
        "/v4/posts",
        json={"post": {"body": "Hello!"}, "meta": {"feeds": ["news"]}},
    )


@pytest.mark.asyncio
async def test_get_user_subscription_status_reads_top_level_flag():
    """get_user_subscription_status should read top-level flags."""
    api = FreeFeedAPI("test-token")

    mock_response = {"youAreSubscribed": True}

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        result = await api.get_user_subscription_status("alice")

        assert result is True
        mock_client.get.assert_called_once_with("/v4/users/alice")


@pytest.mark.asyncio
async def test_get_user_subscription_status_reads_user_object_flag():
    """get_user_subscription_status should read flags from user object."""
    api = FreeFeedAPI("test-token")

    mock_response = {"users": {"youAreSubscribed": False}}

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        result = await api.get_user_subscription_status("alice")

        assert result is False
        mock_client.get.assert_called_once_with("/v4/users/alice")


@pytest.mark.asyncio
async def test_get_user_subscription_status_reads_you_can_unsubscribe():
    """get_user_subscription_status should detect subscriptions via youCan."""
    api = FreeFeedAPI("test-token")

    mock_response = {"users": {"youCan": ["unsubscribe", "dm"]}}

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        result = await api.get_user_subscription_status("alice")

        assert result is True
        mock_client.get.assert_called_once_with("/v4/users/alice")


@pytest.mark.asyncio
async def test_get_notifications_denormalizes_users():
    """get_notifications should parse notifications and attach users."""
    api = FreeFeedAPI("test-token")

    mock_response = {
        "Notifications": [
            {
                "id": "n1",
                "eventId": "e1",
                "event_type": "post_like",
                "date": "2026-01-25T21:03:38.187Z",
                "created_user_id": "u1",
                "post_id": "p1",
            }
        ],
        "users": [
            {
                "id": "u1",
                "username": "alice",
                "screenName": "Alice",
                "type": "user",
            }
        ],
    }

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        notifications = await api.get_notifications()

        assert len(notifications) == 1
        notif = notifications[0]
        assert notif.event_type == "post_like"
        assert notif.created_user is not None
        assert notif.created_user.username == "alice"


@pytest.mark.asyncio
async def test_get_unread_notifications_count_reads_whoami():
    """get_unread_notifications_count should read whoami."""
    api = FreeFeedAPI("test-token")

    mock_response = {"unreadNotificationsNumber": 5, "unreadDirectsNumber": 2}

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        count = await api.get_unread_notifications_count()

        assert count == 5
        mock_client.get.assert_called_once_with("/v4/users/whoami")


@pytest.mark.asyncio
async def test_get_unread_directs_count_reads_whoami():
    """get_unread_directs_count should read whoami."""
    api = FreeFeedAPI("test-token")

    mock_response = {"unreadNotificationsNumber": 5, "unreadDirectsNumber": 2}

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        count = await api.get_unread_directs_count()

        assert count == 2
        mock_client.get.assert_called_once_with("/v4/users/whoami")
