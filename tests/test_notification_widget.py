"""Tests for NotificationBlock widget."""

from datetime import datetime

import pytest
from textual.app import App
from textual.widgets import Button

from freefood.models import Notification, User
from freefood.widgets.notification import NotificationBlock


def make_user(username: str = "alice", user_type: str = "user") -> User:
    """Create a test user."""
    return User(
        id="u1",
        username=username,
        screen_name=username.title(),
        type=user_type,
    )


@pytest.mark.asyncio
async def test_notification_post_like_format():
    """NotificationBlock should format post_like event."""
    from textual.widgets import Static

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
    from textual.widgets import Static

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


@pytest.mark.asyncio
async def test_notification_block_does_not_expand_height():
    """NotificationBlock should not expand to full screen height."""
    from textual.app import App

    notif = Notification(
        id="n3",
        event_id="e3",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id="p3",
        comment_id=None,
    )

    class TestApp(App):
        def compose(self):
            yield NotificationBlock(notif)

    async with TestApp().run_test(size=(80, 20)) as pilot:
        app = pilot.app
        block = app.query_one(NotificationBlock)
        assert block.region.height < 20


@pytest.mark.asyncio
async def test_notification_buttons_not_focusable_outside_post_mode():
    """Notification buttons should not be focusable outside post mode."""
    from textual.app import App
    from textual.widgets import Button

    notif = Notification(
        id="n4",
        event_id="e4",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id="p4",
        comment_id=None,
    )

    class TestApp(App):
        def compose(self):
            yield NotificationBlock(notif)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        block = app.query_one(NotificationBlock)
        for btn in block.query(Button):
            assert btn.can_focus is False


@pytest.mark.asyncio
async def test_notification_buttons_focusable_in_post_mode():
    """Notification buttons should be focusable in post mode."""
    from textual.app import App
    from textual.widgets import Button

    notif = Notification(
        id="n5",
        event_id="e5",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id="p5",
        comment_id=None,
    )

    class TestApp(App):
        def compose(self):
            yield NotificationBlock(notif)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        block = app.query_one(NotificationBlock)
        block.focus()
        await pilot.press("enter")
        await pilot.pause()
        for btn in block.query(Button):
            assert btn.can_focus is True


@pytest.mark.asyncio
async def test_notification_enter_focuses_first_button():
    """Enter should focus first button in post mode."""
    from textual.app import App

    notif = Notification(
        id="n6",
        event_id="e6",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id="p6",
        comment_id=None,
    )

    class TestApp(App):
        def compose(self):
            yield NotificationBlock(notif)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        block = app.query_one(NotificationBlock)
        block.focus()
        await pilot.press("enter")
        await pilot.pause()
        assert app.focused.id == "user-link-notification-user-alice"


@pytest.mark.asyncio
async def test_notification_tab_stays_within_block():
    """Tab should stay within notification in post mode."""
    from textual.containers import Vertical

    notif1 = Notification(
        id="n7",
        event_id="e7",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id="p7",
        comment_id=None,
    )
    notif2 = Notification(
        id="n8",
        event_id="e8",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("bob"),
        post_id="p8",
        comment_id=None,
    )

    class TestApp(App):
        def compose(self):
            with Vertical():
                yield NotificationBlock(notif1)
                yield NotificationBlock(notif2)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        first = app.query(NotificationBlock).first()
        first.focus()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("tab")
        await pilot.pause()
        focused = app.focused
        assert first.is_ancestor_of(focused)


# --- compose with user=None (lines 109-111) ---


@pytest.mark.asyncio
async def test_notification_unknown_user_renders():
    """NotificationBlock should render @unknown when created_user is None."""
    notif = Notification(
        id="n10",
        event_id="e10",
        event_type="post_like",
        date=datetime.now(),
        created_user=None,
        post_id="p10",
        comment_id=None,
    )

    class TestApp(App):
        def compose(self):
            yield NotificationBlock(notif)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        block = app.query_one(NotificationBlock)
        # Find the @unknown button
        buttons = list(block.query(Button))
        unknown_btn = [b for b in buttons if b.label.plain == "@unknown"]
        assert len(unknown_btn) == 1
        # The unknown button should not be focusable
        assert unknown_btn[0].can_focus is False


# --- action_exit_post_mode (lines 143-146) ---


@pytest.mark.asyncio
async def test_notification_escape_exits_post_mode():
    """Escape in post mode should exit back to block focus."""
    notif = Notification(
        id="n11",
        event_id="e11",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id="p11",
        comment_id=None,
    )

    class TestApp(App):
        def compose(self):
            yield NotificationBlock(notif)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        block = app.query_one(NotificationBlock)
        block.focus()
        # Enter post mode
        await pilot.press("enter")
        await pilot.pause()
        assert block.post_mode is True
        assert block.has_class("post-mode")

        # Press escape to exit
        await pilot.press("escape")
        await pilot.pause()
        assert block.post_mode is False
        assert not block.has_class("post-mode")
        assert app.focused is block


# --- on_key with focused is None or focused is self (line 161) ---


@pytest.mark.asyncio
async def test_notification_on_key_not_in_post_mode_returns():
    """on_key should return early when not in post mode."""
    notif = Notification(
        id="n12",
        event_id="e12",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id="p12",
        comment_id=None,
    )

    class TestApp(App):
        def compose(self):
            yield NotificationBlock(notif)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        block = app.query_one(NotificationBlock)
        block.focus()
        await pilot.pause()
        # Not in post mode, pressing tab should not crash
        await pilot.press("tab")
        await pilot.pause()


# --- on_key with focused not ancestor (line 163) ---


@pytest.mark.asyncio
async def test_notification_on_key_focus_outside_block():
    """on_key should ignore focus outside the notification block."""
    from textual.containers import Vertical

    notif1 = Notification(
        id="n13",
        event_id="e13",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id="p13",
        comment_id=None,
    )
    notif2 = Notification(
        id="n14",
        event_id="e14",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("bob"),
        post_id="p14",
        comment_id=None,
    )

    class TestApp(App):
        def compose(self):
            with Vertical():
                yield NotificationBlock(notif1)
                yield NotificationBlock(notif2)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        blocks = list(app.query(NotificationBlock))
        first = blocks[0]
        second = blocks[1]

        # Enter post mode on first block
        first.focus()
        await pilot.press("enter")
        await pilot.pause()

        # Now manually focus the second block (outside first)
        second.focus()
        await pilot.pause()

        # first is still in post_mode but focus is outside
        assert first.post_mode is True
        assert not first.is_ancestor_of(app.focused)


# --- on_key navigation: up/left/shift+tab going back (lines 168-172) ---


@pytest.mark.asyncio
async def test_notification_shift_tab_navigates_back():
    """shift+tab should navigate to previous focusable in post mode."""
    notif = Notification(
        id="n15",
        event_id="e15",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id="p15",
        comment_id=None,
    )

    class TestApp(App):
        def compose(self):
            yield NotificationBlock(notif)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        block = app.query_one(NotificationBlock)
        block.focus()
        await pilot.press("enter")
        await pilot.pause()

        # Move forward to view-post button
        await pilot.press("tab")
        await pilot.pause()
        assert app.focused.id == "btn-view-post"

        # Now go back with shift+tab
        await pilot.press("shift+tab")
        await pilot.pause()
        assert app.focused.id == "user-link-notification-user-alice"


@pytest.mark.asyncio
async def test_notification_up_navigates_back():
    """up key should navigate to previous focusable in post mode."""
    notif = Notification(
        id="n16",
        event_id="e16",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id="p16",
        comment_id=None,
    )

    class TestApp(App):
        def compose(self):
            yield NotificationBlock(notif)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        block = app.query_one(NotificationBlock)
        block.focus()
        await pilot.press("enter")
        await pilot.pause()

        # Move forward
        await pilot.press("tab")
        await pilot.pause()

        # Go back with up
        await pilot.press("up")
        await pilot.pause()
        assert app.focused.id == "user-link-notification-user-alice"


@pytest.mark.asyncio
async def test_notification_shift_tab_at_first_stays():
    """shift+tab at first focusable should stay put."""
    notif = Notification(
        id="n17",
        event_id="e17",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id="p17",
        comment_id=None,
    )

    class TestApp(App):
        def compose(self):
            yield NotificationBlock(notif)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        block = app.query_one(NotificationBlock)
        block.focus()
        await pilot.press("enter")
        await pilot.pause()

        # At first button
        assert app.focused.id == "user-link-notification-user-alice"

        # shift+tab should stay at first
        await pilot.press("shift+tab")
        await pilot.pause()
        assert app.focused.id == "user-link-notification-user-alice"


# --- is_ancestor_of returns False (line 190) ---


def test_notification_is_ancestor_of_returns_false():
    """is_ancestor_of should return False for unrelated widgets."""
    notif = Notification(
        id="n18",
        event_id="e18",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id=None,
        comment_id=None,
    )
    block = NotificationBlock(notif)
    other = NotificationBlock(notif)
    assert block.is_ancestor_of(other) is False


# --- _format_tail with various event types ---


def test_notification_format_tail_all_event_types():
    """_format_tail should return correct text for each event type."""
    event_templates = {
        "direct_comment": "commented on your post",
        "post_comment": "commented on a post",
        "mention_in_post": "mentioned you in a post",
        "mention_in_comment": "mentioned you in a comment",
        "mention_comment_to": "mentioned you in a comment",
        "post_like": "liked your post",
        "subscription": "subscribed to you",
        "backlink_in_post": "mentioned your post",
        "unknown_type": "unknown_type",
    }
    for event_type, expected_tail in event_templates.items():
        notif = Notification(
            id="n_type",
            event_id="e_type",
            event_type=event_type,
            date=datetime.now(),
            created_user=make_user("alice"),
            post_id=None,
            comment_id=None,
        )
        block = NotificationBlock(notif)
        assert block._format_tail() == expected_tail


# --- Notification with no post_id (no view-post button) ---


@pytest.mark.asyncio
async def test_notification_no_post_id_no_view_post_button():
    """When post_id is None, no view-post button should be rendered."""
    from textual.css.query import NoMatches

    notif = Notification(
        id="n19",
        event_id="e19",
        event_type="subscription",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id=None,
        comment_id=None,
    )

    class TestApp(App):
        def compose(self):
            yield NotificationBlock(notif)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        block = app.query_one(NotificationBlock)
        with pytest.raises(NoMatches):
            block.query_one("#btn-view-post", Button)


# --- on_button_pressed for btn-view-post when post_id is None ---


def test_notification_view_post_no_post_id_no_message():
    """btn-view-post click without post_id should not emit PostClicked."""
    from unittest.mock import Mock, patch

    notif = Notification(
        id="n20",
        event_id="e20",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id=None,
        comment_id=None,
    )
    widget = NotificationBlock(notif)

    mock_button = Mock(spec=Button)
    mock_button.id = "btn-view-post"
    mock_event = Mock(spec=Button.Pressed)
    mock_event.button = mock_button

    with patch.object(widget, "post_message") as mock_post_message:
        widget.on_button_pressed(mock_event)

    mock_post_message.assert_not_called()


# --- on_button_pressed with user-link that has wrong format ---


def test_notification_user_link_bad_format_no_message():
    """User link with wrong id format should not emit UserClicked."""
    from unittest.mock import Mock, patch

    notif = Notification(
        id="n21",
        event_id="e21",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id=None,
        comment_id=None,
    )
    widget = NotificationBlock(notif)

    # user-link- prefix but only 2 parts instead of 3
    mock_button = Mock(spec=Button)
    mock_button.id = "user-link-bad"
    mock_event = Mock(spec=Button.Pressed)
    mock_event.button = mock_button

    with patch.object(widget, "post_message") as mock_post_message:
        widget.on_button_pressed(mock_event)

    mock_post_message.assert_not_called()


# --- on_button_pressed with button.id is None ---


def test_notification_button_press_none_id():
    """Button press with None id should not crash."""
    from unittest.mock import Mock, patch

    notif = Notification(
        id="n22",
        event_id="e22",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id="p22",
        comment_id=None,
    )
    widget = NotificationBlock(notif)

    mock_button = Mock(spec=Button)
    mock_button.id = None
    mock_event = Mock(spec=Button.Pressed)
    mock_event.button = mock_button

    with patch.object(widget, "post_message") as mock_post_message:
        widget.on_button_pressed(mock_event)

    mock_post_message.assert_not_called()


# --- tab at last element stays in block ---


@pytest.mark.asyncio
async def test_notification_tab_at_last_stays():
    """Tab at last focusable in notification should stay put."""
    notif = Notification(
        id="n23",
        event_id="e23",
        event_type="post_like",
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id="p23",
        comment_id=None,
    )

    class TestApp(App):
        def compose(self):
            yield NotificationBlock(notif)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        block = app.query_one(NotificationBlock)
        block.focus()
        await pilot.press("enter")
        await pilot.pause()

        # Navigate to last button (btn-view-post)
        await pilot.press("tab")
        await pilot.pause()
        assert app.focused.id == "btn-view-post"

        # Tab again - should stay at btn-view-post
        await pilot.press("tab")
        await pilot.pause()
        assert app.focused.id == "btn-view-post"


# --- _focus_first_button when no buttons are focusable ---


@pytest.mark.asyncio
async def test_notification_focus_first_button_no_focusable():
    """_focus_first_button should handle case when no buttons are focusable."""
    notif = Notification(
        id="n24",
        event_id="e24",
        event_type="subscription",
        date=datetime.now(),
        created_user=None,
        post_id=None,
        comment_id=None,
    )

    class TestApp(App):
        def compose(self):
            yield NotificationBlock(notif)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        block = app.query_one(NotificationBlock)
        # No buttons should be focusable since user is None and no post_id
        # Calling _focus_first_button should not crash
        block._focus_first_button()
        await pilot.pause()
