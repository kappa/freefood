"""Tests for FreeFeed ResponseParser."""

import pytest

from freefood.models import User
from freefood.parsers import ResponseParser


@pytest.fixture
def parser():
    """Create a parser instance."""
    return ResponseParser("https://freefeed.net")


def test_parser_initialization(parser):
    """Parser should initialize with base URL."""
    assert parser.base_url == "https://freefeed.net"


def test_parse_user(parser):
    """parse_user should return User object."""
    data = {
        "id": "user-123",
        "username": "testuser",
        "screenName": "Test User",
        "type": "user",
        "profilePictureMediumUrl": "http://example.com/pic.jpg",
    }
    user = parser.parse_user(data)
    assert user.id == "user-123"
    assert user.username == "testuser"
    assert user.screen_name == "Test User"
    assert user.type == "user"
    assert user.profile_picture_url == "http://example.com/pic.jpg"


def test_denormalize_posts(parser):
    """denormalize_posts should join normalized data."""
    current_user = User(
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
            {
                "id": "user-1",
                "username": "alice",
                "screenName": "Alice",
                "type": "user",
            },
            {"id": "user-2", "username": "bob", "screenName": "Bob", "type": "user"},
            {"id": "feed-1", "username": "news", "screenName": "News", "type": "group"},
        ],
    }

    posts = parser.denormalize_posts(normalized_data, current_user)

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


def test_denormalize_posts_sets_direct_recipients(parser):
    """denormalize_posts should map direct recipients from subscriptions."""
    current_user = User(
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
            {
                "id": "user-1",
                "username": "alice",
                "screenName": "Alice",
                "type": "user",
            },
            {"id": "user-2", "username": "bob", "screenName": "Bob", "type": "user"},
        ],
        "subscriptions": [
            {"id": "direct-1", "name": "Directs", "user": "user-1"},
            {"id": "direct-2", "name": "Directs", "user": "user-2"},
        ],
    }

    posts = parser.denormalize_posts(normalized_data, current_user)

    assert [u.username for u in posts[0].direct_recipients] == ["bob"]


def test_get_attachment_url_explicit(parser):
    """get_attachment_url should use provided url."""
    data = {"id": "att1", "url": "/v4/attachments/att1/original"}
    url = parser.get_attachment_url(data)
    # httpx.URL.join makes it absolute
    assert url == "https://freefeed.net/v4/attachments/att1/original"


def test_get_attachment_url_constructed(parser):
    """get_attachment_url should construct /original URL if url is missing."""
    data = {"id": "att1"}
    url = parser.get_attachment_url(data)
    assert "/v4/attachments/att1/original?redirect=" in url


def test_get_attachment_url_missing_id(parser):
    """get_attachment_url should return None if ID is missing."""
    data = {"fileName": "test.jpg"}
    url = parser.get_attachment_url(data)
    assert url is None


def test_denormalize_posts_includes_attachments(parser):
    """denormalize_posts should include attachments."""
    current_user = User(id="me", username="me", screen_name="Me", type="user")

    normalized_data = {
        "posts": [
            {
                "id": "p1",
                "body": "Post with attachment",
                "createdBy": "me",
                "createdAt": "1706097600000",
                "updatedAt": "1706097600000",
                "comments": [],
                "likes": [],
                "postedTo": [],
                "attachments": ["att1"],
                "omittedComments": 0,
                "omittedLikes": 0,
            }
        ],
        "attachments": [
            {
                "id": "att1",
                "fileName": "test.jpg",
                "fileSize": 1024,
                "mediaType": "image/jpeg",
            }
        ],
        "users": [{"id": "me", "username": "me", "screenName": "Me", "type": "user"}],
    }

    posts = parser.denormalize_posts(normalized_data, current_user)

    assert len(posts) == 1
    post = posts[0]
    assert len(post.attachments) == 1
    att = post.attachments[0]
    assert att.id == "att1"
    assert att.file_name == "test.jpg"
    assert "/v4/attachments/att1/original?redirect=" in att.url


def test_parse_notifications_denormalizes_users(parser):
    """parse_notifications should parse notifications and attach users."""
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

    notifications = parser.parse_notifications(mock_response)

    assert len(notifications) == 1
    notif = notifications[0]
    assert notif.event_type == "post_like"
    assert notif.created_user is not None
    assert notif.created_user.username == "alice"


def test_parse_notifications_handles_null_date(parser):
    """parse_notifications should fallback when date is None."""
    data = {
        "Notifications": [
            {
                "id": "n1",
                "eventId": "e1",
                "event_type": "test",
                "date": None,
                "createdAt": "1706097600000",
            }
        ],
        "users": [],
    }

    notifications = parser.parse_notifications(data)

    assert len(notifications) == 1
    assert notifications[0].date is not None
