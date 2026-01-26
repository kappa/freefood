"""Tests for NotificationBlock widget."""

from datetime import datetime

import pytest

from freefood.models import Notification, User
from freefood.widgets.notification import NotificationBlock


def make_user(username: str = "alice") -> User:
    """Create a test user."""
    return User(id="u1", username=username, screen_name=username.title(), type="user")


@pytest.mark.asyncio
async def test_notification_post_like_format():
    """NotificationBlock should format post_like event."""
    from textual.app import App
    from textual.widgets import Static, Button

    notif = Notification(
        id="n1",
        event_id="e1",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id="p1",
        comment_id=None,
    )

    class TestApp(App):
        def compose(self):
            yield NotificationBlock(notif)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        block = app.query_one(NotificationBlock)
        user_button = block.query_one("#user-link-notification-user-alice", Button)
        text = block.query_one(Static).content
        assert user_button.label.plain == "@alice"
        assert "liked your post" in str(text)


def test_notification_user_click_emits_message():
    """User link click should emit UserClicked."""
    from unittest.mock import Mock, patch

    from textual.widgets import Button

    notif = Notification(
        id="n1",
        event_id="e1",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id="p1",
        comment_id=None,
    )
    widget = NotificationBlock(notif)

    mock_button = Mock(spec=Button)
    mock_button.id = "user-link-notification-user-alice"
    mock_event = Mock(spec=Button.Pressed)
    mock_event.button = mock_button

    with patch.object(widget, "post_message") as mock_post_message:
        widget.on_button_pressed(mock_event)

    msg = mock_post_message.call_args[0][0]
    assert isinstance(msg, NotificationBlock.UserClicked)
    assert msg.username == "alice"
    assert msg.user_type == "user"


def test_notification_post_click_emits_message():
    """Post button click should emit PostClicked."""
    from unittest.mock import Mock, patch

    from textual.widgets import Button

    notif = Notification(
        id="n1",
        event_id="e1",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id="p1",
        comment_id=None,
    )
    widget = NotificationBlock(notif)

    mock_button = Mock(spec=Button)
    mock_button.id = "btn-view-post"
    mock_event = Mock(spec=Button.Pressed)
    mock_event.button = mock_button

    with patch.object(widget, "post_message") as mock_post_message:
        widget.on_button_pressed(mock_event)

    msg = mock_post_message.call_args[0][0]
    assert isinstance(msg, NotificationBlock.PostClicked)
    assert msg.post_id == "p1"


@pytest.mark.asyncio
async def test_notification_mention_comment_to_format():
    """NotificationBlock should format mention_comment_to event."""
    from textual.app import App
    from textual.widgets import Static, Button

    notif = Notification(
        id="n2",
        event_id="e2",
        event_type="mention_comment_to",
        date=datetime.now(),
        created_user=make_user("bob"),
        post_id="p2",
        comment_id="c2",
    )

    class TestApp(App):
        def compose(self):
            yield NotificationBlock(notif)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        block = app.query_one(NotificationBlock)
        user_button = block.query_one("#user-link-notification-user-bob", Button)
        text = block.query_one(Static).content
        assert user_button.label.plain == "@bob"
        assert "mentioned you in a comment" in str(text)
