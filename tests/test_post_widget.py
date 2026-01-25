"""Tests for PostBlock widget."""

from datetime import datetime

import pytest

from freefood.models import Post, User, Comment
from freefood.widgets.post import PostBlock, format_time_ago


def make_user(
    id: str = "u1",
    username: str = "alice",
    screen_name: str = "Alice",
    user_type: str = "user",
) -> User:
    """Create a test user."""
    return User(id=id, username=username, screen_name=screen_name, type=user_type)


def make_post(
    id: str = "p1",
    body: str = "Test post body",
    author: User | None = None,
    groups: list[User] | None = None,
    comments: list[Comment] | None = None,
    likes: list[User] | None = None,
    is_liked: bool = False,
    is_hidden: bool = False,
    is_own: bool = False,
    omitted_comments: int = 0,
    omitted_likes: int = 0,
) -> Post:
    """Create a test post."""
    now = datetime.now()
    return Post(
        id=id,
        body=body,
        author=author or make_user(),
        groups=groups or [],
        created_at=now,
        updated_at=now,
        comments=comments or [],
        omitted_comments=omitted_comments,
        omitted_likes=omitted_likes,
        likes=likes or [],
        is_liked=is_liked,
        is_hidden=is_hidden,
        is_own=is_own,
    )


class TestPostBlockMessages:
    """Tests for PostBlock message classes."""

    def test_expand_comments_message_exists(self):
        """ExpandComments message should be defined and instantiable."""
        post = make_post()
        msg = PostBlock.ExpandComments(post)
        assert msg.post is post

    def test_like_requested_message_exists(self):
        """LikeRequested message should be defined and instantiable."""
        post = make_post()
        msg = PostBlock.LikeRequested(post)
        assert msg.post is post

    def test_hide_requested_message_exists(self):
        """HideRequested message should be defined and instantiable."""
        post = make_post()
        msg = PostBlock.HideRequested(post)
        assert msg.post is post

    def test_selected_message_exists(self):
        """Selected message should be defined and instantiable."""
        post = make_post()
        msg = PostBlock.Selected(post)
        assert msg.post is post


class TestPostBlockBindings:
    """Tests for PostBlock keyboard bindings."""

    def test_bindings_defined(self):
        """BINDINGS should be defined on PostBlock."""
        assert hasattr(PostBlock, "BINDINGS")
        assert isinstance(PostBlock.BINDINGS, list)

    def test_bindings_contains_up(self):
        """BINDINGS should contain 'up' binding."""
        binding_keys = [b[0] for b in PostBlock.BINDINGS]
        assert "up" in binding_keys

    def test_bindings_contains_down(self):
        """BINDINGS should contain 'down' binding."""
        binding_keys = [b[0] for b in PostBlock.BINDINGS]
        assert "down" in binding_keys

    def test_bindings_contains_enter(self):
        """BINDINGS should contain 'enter' binding for post mode."""
        binding_keys = [b[0] for b in PostBlock.BINDINGS]
        assert "enter" in binding_keys

    def test_up_binding_action(self):
        """Up binding should map to focus_previous action."""
        for binding in PostBlock.BINDINGS:
            if binding[0] == "up":
                assert binding[1] == "focus_previous"
                return
        pytest.fail("up binding not found")

    def test_down_binding_action(self):
        """Down binding should map to focus_next action."""
        for binding in PostBlock.BINDINGS:
            if binding[0] == "down":
                assert binding[1] == "focus_next"
                return
        pytest.fail("down binding not found")

    def test_on_key_method_exists(self):
        """PostBlock should have on_key method for escape handling in post mode."""
        assert hasattr(PostBlock, "on_key")
        assert callable(getattr(PostBlock, "on_key"))


class TestPostBlockConstants:
    """Tests for PostBlock constants."""

    def test_max_body_lines_defined(self):
        """MAX_BODY_LINES should be defined."""
        assert hasattr(PostBlock, "MAX_BODY_LINES")
        assert PostBlock.MAX_BODY_LINES == 50

    def test_max_comment_lines_defined(self):
        """MAX_COMMENT_LINES should be defined."""
        assert hasattr(PostBlock, "MAX_COMMENT_LINES")
        assert PostBlock.MAX_COMMENT_LINES == 10


class TestPostBlockBodyTruncation:
    """Tests for body truncation logic."""

    def test_body_is_truncated_short_body(self):
        """_body_is_truncated should return False for short body."""
        post = make_post(body="Short body")
        widget = PostBlock(post)
        assert widget._body_is_truncated() is False

    def test_body_is_truncated_exactly_max_lines(self):
        """_body_is_truncated should return False when body is exactly MAX_BODY_LINES."""
        lines = ["Line"] * PostBlock.MAX_BODY_LINES
        body = "\n".join(lines)
        post = make_post(body=body)
        widget = PostBlock(post)
        assert widget._body_is_truncated() is False

    def test_body_is_truncated_exceeds_max_lines(self):
        """_body_is_truncated should return True when body exceeds MAX_BODY_LINES."""
        lines = ["Line"] * (PostBlock.MAX_BODY_LINES + 1)
        body = "\n".join(lines)
        post = make_post(body=body)
        widget = PostBlock(post)
        assert widget._body_is_truncated() is True

    def test_body_is_truncated_after_expansion(self):
        """_body_is_truncated should return False when body_expanded is True."""
        lines = ["Line"] * (PostBlock.MAX_BODY_LINES + 10)
        body = "\n".join(lines)
        post = make_post(body=body)
        widget = PostBlock(post)
        widget.body_expanded = True
        assert widget._body_is_truncated() is False


class TestPostBlockFormatting:
    """Tests for post formatting methods."""

    def test_format_header_simple(self):
        """_format_header should format author correctly."""
        author = make_user(username="alice")
        post = make_post(author=author, groups=[])
        widget = PostBlock(post)
        header = widget._format_header()
        assert "@alice wrote:" in header

    def test_format_header_with_group(self):
        """_format_header should include group when present."""
        author = make_user(username="alice")
        group = make_user(id="g1", username="news", user_type="group")
        post = make_post(author=author, groups=[group])
        widget = PostBlock(post)
        header = widget._format_header()
        assert "@alice wrote in @news:" in header

    def test_format_header_unknown_author(self):
        """_format_header should handle None author."""
        post = make_post()
        post.author = None
        widget = PostBlock(post)
        header = widget._format_header()
        assert "@unknown wrote:" in header

    def test_format_body_short(self):
        """_format_body should return full body when short."""
        post = make_post(body="Short body text")
        widget = PostBlock(post)
        assert widget._format_body() == "Short body text"

    def test_format_body_truncated(self):
        """_format_body should truncate long body and add indicator."""
        lines = ["Line {}".format(i) for i in range(PostBlock.MAX_BODY_LINES + 10)]
        body = "\n".join(lines)
        post = make_post(body=body)
        widget = PostBlock(post)
        formatted = widget._format_body()
        assert "[show more...]" in formatted
        # Should only contain MAX_BODY_LINES lines before the indicator
        output_lines = formatted.split("\n")
        # Last line is "[show more...]", so should have MAX_BODY_LINES + 1 total
        assert len(output_lines) == PostBlock.MAX_BODY_LINES + 1

    def test_format_body_expanded(self):
        """_format_body should return full body when expanded."""
        lines = ["Line {}".format(i) for i in range(PostBlock.MAX_BODY_LINES + 10)]
        body = "\n".join(lines)
        post = make_post(body=body)
        widget = PostBlock(post)
        widget.body_expanded = True
        assert widget._format_body() == body


class TestPostBlockLikesFormatting:
    """Tests for likes formatting."""

    def test_format_likes_single(self):
        """_format_likes should format single like."""
        liker = make_user(username="bob")
        post = make_post(likes=[liker])
        widget = PostBlock(post)
        likes_text = widget._format_likes()
        assert "@bob liked this" in likes_text

    def test_format_likes_few(self):
        """_format_likes should list all names when 3 or fewer."""
        likers = [
            make_user(id="1", username="bob"),
            make_user(id="2", username="carol"),
            make_user(id="3", username="dave"),
        ]
        post = make_post(likes=likers)
        widget = PostBlock(post)
        likes_text = widget._format_likes()
        assert "@bob" in likes_text
        assert "@carol" in likes_text
        assert "@dave" in likes_text
        assert "liked this" in likes_text

    def test_format_likes_many(self):
        """_format_likes should summarize when more than 3 likes."""
        likers = [
            make_user(id="1", username="bob"),
            make_user(id="2", username="carol"),
            make_user(id="3", username="dave"),
            make_user(id="4", username="eve"),
        ]
        post = make_post(likes=likers, omitted_likes=5)
        widget = PostBlock(post)
        likes_text = widget._format_likes()
        assert "@bob" in likes_text
        assert "@carol" in likes_text
        assert "@dave" in likes_text
        assert "@eve" not in likes_text  # 4th person not listed by name
        assert "and 6 others liked this" in likes_text  # 1 + 5 omitted = 6


class TestPostBlockCanFocus:
    """Tests for PostBlock focus capability."""

    def test_can_focus_enabled(self):
        """PostBlock should have can_focus=True."""
        # Check that PostBlock is created with can_focus capability
        # In Textual, can_focus is set at class definition
        post = make_post()
        widget = PostBlock(post)
        assert widget.can_focus is True


class TestFormatTimeAgo:
    """Tests for format_time_ago helper function."""

    def test_just_now(self):
        """format_time_ago should return 'just now' for recent times."""
        now = datetime.now()
        assert format_time_ago(now) == "just now"

    def test_minutes_ago(self):
        """format_time_ago should format minutes."""
        from datetime import timedelta

        past = datetime.now() - timedelta(minutes=5)
        result = format_time_ago(past)
        assert "m ago" in result

    def test_hours_ago(self):
        """format_time_ago should format hours."""
        from datetime import timedelta

        past = datetime.now() - timedelta(hours=3)
        result = format_time_ago(past)
        assert "h ago" in result

    def test_days_ago(self):
        """format_time_ago should format days."""
        from datetime import timedelta

        past = datetime.now() - timedelta(days=2)
        result = format_time_ago(past)
        assert "d ago" in result


class TestPostBlockInitialization:
    """Tests for PostBlock initialization."""

    def test_init_stores_post(self):
        """PostBlock should store the post on initialization."""
        post = make_post()
        widget = PostBlock(post)
        assert widget.post is post

    def test_init_body_not_expanded(self):
        """PostBlock should start with body_expanded=False."""
        post = make_post()
        widget = PostBlock(post)
        assert widget.body_expanded is False

    def test_init_comments_not_expanded(self):
        """PostBlock should start with comments_expanded=False."""
        post = make_post()
        widget = PostBlock(post)
        assert widget.comments_expanded is False


class TestPostBlockOwnPostButtons:
    """Tests for own post button visibility.

    Note: These tests verify the logic that would show Edit/Delete buttons
    for posts where is_own=True. The actual compose() method yields these
    buttons conditionally based on post.is_own.
    """

    def test_is_own_flag_accessible(self):
        """PostBlock should be able to access is_own flag from post."""
        post = make_post(is_own=True)
        widget = PostBlock(post)
        assert widget.post.is_own is True

    def test_is_own_false_by_default(self):
        """Posts should have is_own=False by default."""
        post = make_post()
        widget = PostBlock(post)
        assert widget.post.is_own is False


class TestPostBlockComposeActionButtons:
    """Tests for action button rendering in compose().

    These tests use Textual's async testing framework to mount the widget
    in a real App context, then query the widget tree for buttons.
    """

    @pytest.mark.asyncio
    async def test_action_buttons_rendered(self):
        """PostBlock should render Comment, Like, Hide action buttons."""
        from textual.app import App

        post = make_post()

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            # Query for buttons by ID
            btn_comment = app.query_one("#btn-comment")
            btn_like = app.query_one("#btn-like")
            btn_hide = app.query_one("#btn-hide")

            assert btn_comment is not None
            assert btn_like is not None
            assert btn_hide is not None

    @pytest.mark.asyncio
    async def test_edit_delete_buttons_when_is_own_true(self):
        """Edit and Delete buttons should be rendered when is_own=True."""
        from textual.app import App

        post = make_post(is_own=True)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            btn_edit = app.query_one("#btn-edit")
            btn_delete = app.query_one("#btn-delete")

            assert btn_edit is not None
            assert btn_delete is not None

    @pytest.mark.asyncio
    async def test_edit_delete_buttons_not_when_is_own_false(self):
        """Edit and Delete buttons should NOT be rendered when is_own=False."""
        from textual.app import App
        from textual.css.query import NoMatches

        post = make_post(is_own=False)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            # These should raise NoMatches since buttons don't exist
            with pytest.raises(NoMatches):
                app.query_one("#btn-edit")
            with pytest.raises(NoMatches):
                app.query_one("#btn-delete")


class TestPostBlockShowMoreButton:
    """Tests for Show More button rendering."""

    @pytest.mark.asyncio
    async def test_show_more_button_when_body_truncated(self):
        """Show more button should be rendered when body exceeds MAX_BODY_LINES."""
        from textual.app import App

        lines = ["Line"] * (PostBlock.MAX_BODY_LINES + 10)
        body = "\n".join(lines)
        post = make_post(body=body)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            show_more_btn = app.query_one("#show-more-body")
            assert show_more_btn is not None
            assert show_more_btn.label.plain == "Show more..."

    @pytest.mark.asyncio
    async def test_no_show_more_button_when_body_short(self):
        """Show more button should NOT be rendered when body is short."""
        from textual.app import App
        from textual.css.query import NoMatches

        post = make_post(body="Short body")

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            with pytest.raises(NoMatches):
                app.query_one("#show-more-body")


class TestPostBlockOnButtonPressed:
    """Tests for on_button_pressed event handler."""

    def test_show_more_body_sets_body_expanded(self):
        """on_button_pressed should set body_expanded=True for show-more-body."""
        from unittest.mock import Mock, patch
        from textual.widgets import Button

        lines = ["Line"] * (PostBlock.MAX_BODY_LINES + 10)
        body = "\n".join(lines)
        post = make_post(body=body)
        widget = PostBlock(post)

        # Verify body is not expanded initially
        assert widget.body_expanded is False

        # Create a mock button pressed event
        mock_button = Mock(spec=Button)
        mock_button.id = "show-more-body"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        # Patch refresh to prevent actual refresh call
        with patch.object(widget, 'refresh'):
            widget.on_button_pressed(mock_event)

        # Verify body_expanded is now True
        assert widget.body_expanded is True

    def test_btn_like_emits_like_requested(self):
        """on_button_pressed should emit LikeRequested when btn-like pressed."""
        from unittest.mock import Mock, patch

        from textual.widgets import Button

        post = make_post()
        widget = PostBlock(post)

        # Create a mock button pressed event
        mock_button = Mock(spec=Button)
        mock_button.id = "btn-like"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        # Patch post_message to capture the message
        with patch.object(widget, "post_message") as mock_post_message:
            widget.on_button_pressed(mock_event)

        # Verify LikeRequested was posted with the correct post
        mock_post_message.assert_called_once()
        msg = mock_post_message.call_args[0][0]
        assert isinstance(msg, PostBlock.LikeRequested)
        assert msg.post is post

    def test_btn_hide_emits_hide_requested(self):
        """on_button_pressed should emit HideRequested when btn-hide pressed."""
        from unittest.mock import Mock, patch

        from textual.widgets import Button

        post = make_post()
        widget = PostBlock(post)

        # Create a mock button pressed event
        mock_button = Mock(spec=Button)
        mock_button.id = "btn-hide"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        # Patch post_message to capture the message
        with patch.object(widget, "post_message") as mock_post_message:
            widget.on_button_pressed(mock_event)

        # Verify HideRequested was posted with the correct post
        mock_post_message.assert_called_once()
        msg = mock_post_message.call_args[0][0]
        assert isinstance(msg, PostBlock.HideRequested)
        assert msg.post is post


class TestPostBlockLikeButtonLabel:
    """Tests for Like button label based on is_liked state."""

    @pytest.mark.asyncio
    async def test_like_button_shows_like_when_not_liked(self):
        """Like button should show 'Like' when post is not liked."""
        from textual.app import App

        post = make_post(is_liked=False)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            btn_like = app.query_one("#btn-like")
            # Button label should contain "Like" but not "Unlike"
            label_text = btn_like.label.plain
            assert "Like" in label_text
            assert "Unlike" not in label_text

    @pytest.mark.asyncio
    async def test_like_button_shows_unlike_when_liked(self):
        """Like button should show 'Unlike' when post is liked."""
        from textual.app import App

        post = make_post(is_liked=True)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            btn_like = app.query_one("#btn-like")
            # Button label should contain "Unlike"
            label_text = btn_like.label.plain
            assert "Unlike" in label_text


class TestPostBlockHideButtonLabel:
    """Tests for Hide button label based on is_hidden state."""

    @pytest.mark.asyncio
    async def test_hide_button_shows_hide_when_not_hidden(self):
        """Hide button should show 'Hide' when post is not hidden."""
        from textual.app import App

        post = make_post(is_hidden=False)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            btn_hide = app.query_one("#btn-hide")
            # Button label should be "Hide" exactly
            label_text = btn_hide.label.plain
            assert label_text == "Hide"

    @pytest.mark.asyncio
    async def test_hide_button_shows_unhide_when_hidden(self):
        """Hide button should show 'Unhide' when post is hidden."""
        from textual.app import App

        post = make_post(is_hidden=True)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            btn_hide = app.query_one("#btn-hide")
            # Button label should be "Unhide" exactly
            label_text = btn_hide.label.plain
            assert label_text == "Unhide"
