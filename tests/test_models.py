"""Tests for data models."""

from datetime import datetime

from freefood.models import User, Comment, Post, View, HistoryEntry


def test_user_creation():
    """User should be created with required fields."""
    user = User(
        id="123",
        username="alice",
        screen_name="Alice Smith",
        type="user",
    )
    assert user.id == "123"
    assert user.username == "alice"
    assert user.screen_name == "Alice Smith"
    assert user.type == "user"
    assert user.profile_picture_url is None


def test_user_with_profile_picture():
    """User can have optional profile picture."""
    user = User(
        id="123",
        username="alice",
        screen_name="Alice",
        type="user",
        profile_picture_url="https://example.com/pic.jpg",
    )
    assert user.profile_picture_url == "https://example.com/pic.jpg"


def test_group_user():
    """User with type='group' represents a group."""
    group = User(
        id="456",
        username="devs",
        screen_name="Developers",
        type="group",
    )
    assert group.type == "group"


def test_comment_creation():
    """Comment should be created with required fields."""
    author = User(id="1", username="bob", screen_name="Bob", type="user")
    comment = Comment(
        id="c1",
        body="Great post!",
        author=author,
        created_at=datetime(2026, 1, 24, 12, 0, 0),
        likes=5,
    )
    assert comment.id == "c1"
    assert comment.body == "Great post!"
    assert comment.author.username == "bob"
    assert comment.likes == 5
    assert comment.is_liked is False
    assert comment.is_own is False


def test_comment_own_flag():
    """Comment can be marked as user's own."""
    author = User(id="1", username="me", screen_name="Me", type="user")
    comment = Comment(
        id="c1",
        body="My comment",
        author=author,
        created_at=datetime.now(),
        likes=0,
        is_own=True,
    )
    assert comment.is_own is True


def test_post_creation():
    """Post should be created with required fields."""
    author = User(id="1", username="alice", screen_name="Alice", type="user")
    group = User(id="2", username="news", screen_name="News", type="group")
    now = datetime(2026, 1, 24, 12, 0, 0)

    post = Post(
        id="p1",
        body="Hello world!",
        author=author,
        groups=[group],
        created_at=now,
        updated_at=now,
        comments=[],
        omitted_comments=0,
        omitted_likes=0,
        likes=[],
    )
    assert post.id == "p1"
    assert post.body == "Hello world!"
    assert post.author.username == "alice"
    assert len(post.groups) == 1
    assert post.groups[0].username == "news"
    assert post.is_liked is False
    assert post.is_hidden is False
    assert post.is_own is False


def test_post_with_comments():
    """Post can contain comments."""
    author = User(id="1", username="alice", screen_name="Alice", type="user")
    commenter = User(id="2", username="bob", screen_name="Bob", type="user")
    now = datetime.now()

    comment = Comment(
        id="c1",
        body="Nice!",
        author=commenter,
        created_at=now,
        likes=1,
    )
    post = Post(
        id="p1",
        body="My post",
        author=author,
        groups=[],
        created_at=now,
        updated_at=now,
        comments=[comment],
        omitted_comments=5,
        omitted_likes=10,
        likes=[commenter],
    )
    assert len(post.comments) == 1
    assert post.comments[0].body == "Nice!"
    assert post.omitted_comments == 5
    assert post.omitted_likes == 10
    assert len(post.likes) == 1


def test_view_enum():
    """View enum should have all required values."""
    assert View.HOME.value == "home"
    assert View.NOTIFICATIONS.value == "notifications"
    assert View.DIRECTS.value == "directs"
    assert View.SEARCH.value == "search"
    assert View.USER_FEED.value == "user_feed"
    assert View.GROUP_FEED.value == "group_feed"


def test_history_entry():
    """HistoryEntry should store navigation state."""
    entry = HistoryEntry(
        view=View.USER_FEED,
        target="alice",
        scroll_position=42,
        query=None,
    )
    assert entry.view == View.USER_FEED
    assert entry.target == "alice"
    assert entry.scroll_position == 42


def test_history_entry_for_search():
    """HistoryEntry for search should store query."""
    entry = HistoryEntry(
        view=View.SEARCH,
        target=None,
        scroll_position=0,
        query="python",
    )
    assert entry.query == "python"
