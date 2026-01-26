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
    omitted_comments_offset: int = 0,
    omitted_comment_likes: int = 0,
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
        omitted_comments_offset=omitted_comments_offset,
        omitted_comment_likes=omitted_comment_likes,
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

    def test_user_clicked_message_exists(self):
        """UserClicked message should be defined and instantiable."""
        msg = PostBlock.UserClicked("alice", "user")
        assert msg.username == "alice"
        assert msg.user_type == "user"


class TestPostBlockBindings:
    """Tests for PostBlock keyboard bindings."""

    def test_bindings_defined(self):
        """BINDINGS should be defined on PostBlock."""
        assert hasattr(PostBlock, "BINDINGS")
        assert isinstance(PostBlock.BINDINGS, list)

    def test_bindings_contains_enter(self):
        """BINDINGS should contain 'enter' binding for post mode."""
        binding_keys = [b[0] for b in PostBlock.BINDINGS]
        assert "enter" in binding_keys

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

    def test_user_link_emits_user_clicked(self):
        """on_button_pressed should emit UserClicked when a user link is pressed."""
        from unittest.mock import Mock, patch

        from textual.widgets import Button

        widget = PostBlock(make_post())

        mock_button = Mock(spec=Button)
        mock_button.id = "user-link-user-alice"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "post_message") as mock_post_message:
            widget.on_button_pressed(mock_event)

        mock_post_message.assert_called_once()
        msg = mock_post_message.call_args[0][0]
        assert isinstance(msg, PostBlock.UserClicked)
        assert msg.username == "alice"
        assert msg.user_type == "user"


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


def make_comment(
    id: str = "c1",
    body: str = "Test comment",
    author: User | None = None,
    likes: int = 0,
) -> Comment:
    """Create a test comment."""
    return Comment(
        id=id,
        body=body,
        author=author or make_user(username="commenter"),
        created_at=datetime.now(),
        likes=likes,
    )


class TestCommentBlockFocusable:
    """Tests for focusable comments in post mode."""

    @pytest.mark.asyncio
    async def test_comments_are_focusable_in_post_mode(self):
        """Comments should be focusable when in post mode."""
        from textual.app import App

        comment = make_comment()
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            # Enter post mode
            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Find comment widgets - they should be focusable
            from freefood.widgets.post import CommentBlock

            comment_widgets = list(app.query(CommentBlock))
            assert len(comment_widgets) > 0, "No CommentBlock widgets found"

            # Comments should be focusable in post mode
            for cw in comment_widgets:
                assert cw.can_focus is True, "Comment should be focusable in post mode"

    @pytest.mark.asyncio
    async def test_comments_not_focusable_outside_post_mode(self):
        """Comments should NOT be focusable when not in post mode."""
        from textual.app import App

        comment = make_comment()
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            # NOT in post mode
            post_block.focus()
            await pilot.pause()

            # Comments should not be focusable
            from freefood.widgets.post import CommentBlock

            comment_widgets = list(app.query(CommentBlock))
            assert len(comment_widgets) > 0, "No CommentBlock widgets found"

            for cw in comment_widgets:
                assert cw.can_focus is False, "Comment should not be focusable outside post mode"

    @pytest.mark.asyncio
    async def test_can_navigate_to_comment_in_post_mode(self):
        """Should be able to navigate to comments with Tab/arrows in post mode."""
        from textual.app import App

        comment = make_comment()
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            # Enter post mode
            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Navigate past buttons to comment
            # Order should be: Comment btn, Like btn, Hide btn, then CommentBlock(s)
            await pilot.press("tab")  # Comment -> Like
            await pilot.press("tab")  # Like -> Hide
            await pilot.press("tab")  # Hide -> first comment
            await pilot.pause()

            # Should now be focused on a CommentBlock
            from freefood.widgets.post import CommentBlock

            focused = app.focused
            assert isinstance(focused, CommentBlock), f"Expected CommentBlock, got {type(focused)}"


class TestMoreCommentsButton:
    """Tests for 'more comments' button in post mode."""

    @pytest.mark.asyncio
    async def test_more_comments_button_focusable_in_post_mode(self):
        """More comments button should be focusable when in post mode."""
        from textual.app import App
        from textual.widgets import Button

        # Create a post with omitted comments
        post = make_post(omitted_comments=5)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            # Enter post mode
            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Find the more-comments button - it should exist and be focusable
            more_btn = app.query_one("#btn-more-comments", Button)
            assert more_btn is not None, "More comments button not found"
            assert more_btn.can_focus is True, "More comments button should be focusable"

    @pytest.mark.asyncio
    async def test_more_comments_button_not_focusable_outside_post_mode(self):
        """More comments button should NOT be focusable outside post mode."""
        from textual.app import App
        from textual.widgets import Button

        # Create a post with omitted comments
        post = make_post(omitted_comments=5)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            # NOT in post mode - just focus the post
            post_block.focus()
            await pilot.pause()

            # The more-comments button should exist but not be focusable
            more_btn = app.query_one("#btn-more-comments", Button)
            assert more_btn is not None, "More comments button not found"
            assert more_btn.can_focus is False, "More comments button should not be focusable outside post mode"

    @pytest.mark.asyncio
    async def test_can_navigate_to_more_comments_button(self):
        """Should be able to navigate to more comments button in post mode."""
        from textual.app import App
        from textual.widgets import Button

        # Create a post with omitted comments
        post = make_post(omitted_comments=5)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            # Enter post mode
            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Navigate to more-comments button
            # Order: Comment btn, Like btn, Hide btn, then more-comments btn
            await pilot.press("tab")  # Comment -> Like
            await pilot.press("tab")  # Like -> Hide
            await pilot.press("tab")  # Hide -> more-comments
            await pilot.pause()

            # Should be focused on more-comments button
            focused = app.focused
            assert focused.id == "btn-more-comments", f"Expected btn-more-comments, got {focused.id}"

    @pytest.mark.asyncio
    async def test_more_comments_button_with_offset_in_middle(self):
        """More comments button should appear at offset position between comments."""
        from textual.app import App
        from textual.widgets import Button

        # 3 comments with omitted comments at offset 1 (after first comment)
        comments = [make_comment(id=f"c{i}") for i in range(3)]
        post = make_post(
            comments=comments,
            omitted_comments=5,
            omitted_comments_offset=1,
            omitted_comment_likes=10,
        )

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            # Enter post mode
            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Find the more-comments button
            more_btn = app.query_one("#btn-more-comments", Button)
            assert more_btn is not None, "More comments button not found"
            assert more_btn.can_focus is True, "More comments button should be focusable"


class TestPostModeNavigation:
    """Tests for keyboard navigation within post mode."""

    @pytest.mark.asyncio
    async def test_tab_stays_within_post_in_post_mode(self):
        """Tab should not escape post when in post mode."""
        from textual.app import App
        from textual.containers import Vertical

        post1 = make_post(id="p1", body="Post 1")
        post2 = make_post(id="p2", body="Post 2")

        class TestApp(App):
            def compose(self):
                with Vertical():
                    yield PostBlock(post1)
                    yield PostBlock(post2)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block1 = app.query(PostBlock).first()

            # Enter post mode
            post_block1.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Focus should now be on first button (Comment)
            assert app.focused.id == "btn-comment"

            # Press Tab to move to next button
            await pilot.press("tab")
            await pilot.pause()

            # Should move to Like button, NOT escape to post2
            focused = app.focused
            # Verify focus is still within post_block1
            assert post_block1.is_ancestor_of(focused), f"Focus escaped to {focused}"

    @pytest.mark.asyncio
    async def test_shift_tab_stays_within_post_in_post_mode(self):
        """Shift+Tab should not escape post when in post mode."""
        from textual.app import App
        from textual.containers import Vertical

        post1 = make_post(id="p1", body="Post 1")
        post2 = make_post(id="p2", body="Post 2")

        class TestApp(App):
            def compose(self):
                with Vertical():
                    yield PostBlock(post1)
                    yield PostBlock(post2)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block1 = app.query(PostBlock).first()

            # Enter post mode
            post_block1.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Focus should be on first button
            assert app.focused.id == "btn-comment"

            # Press Shift+Tab - should stay at first button (no previous)
            await pilot.press("shift+tab")
            await pilot.pause()

            # Focus should still be within post_block1
            focused = app.focused
            assert post_block1.is_ancestor_of(focused), f"Focus escaped to {focused}"

    @pytest.mark.asyncio
    async def test_left_arrow_navigates_within_post(self):
        """Left arrow should navigate between focusable elements in post."""
        from textual.app import App

        post = make_post()

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            # Enter post mode
            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Move to second button first
            await pilot.press("right")
            await pilot.pause()
            assert app.focused.id == "btn-like"

            # Now press left to go back
            await pilot.press("left")
            await pilot.pause()

            # Should be back at Comment button
            assert app.focused.id == "btn-comment"

    @pytest.mark.asyncio
    async def test_right_arrow_navigates_within_post(self):
        """Right arrow should navigate between focusable elements in post."""
        from textual.app import App

        post = make_post()

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            # Enter post mode
            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Should start at Comment button
            assert app.focused.id == "btn-comment"

            # Press right to move to Like button
            await pilot.press("right")
            await pilot.pause()

            # Should be at Like button
            assert app.focused.id == "btn-like"

    @pytest.mark.asyncio
    async def test_tab_at_last_element_stays_within_post(self):
        """Tab at last focusable element should not escape post."""
        from textual.app import App
        from textual.containers import Vertical

        post1 = make_post(id="p1", body="Post 1")
        post2 = make_post(id="p2", body="Post 2")

        class TestApp(App):
            def compose(self):
                with Vertical():
                    yield PostBlock(post1)
                    yield PostBlock(post2)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block1 = app.query(PostBlock).first()

            # Enter post mode
            post_block1.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Navigate to last button (Hide)
            await pilot.press("tab")  # Comment -> Like
            await pilot.press("tab")  # Like -> Hide
            await pilot.pause()

            assert app.focused.id == "btn-hide"

            # Press Tab at last element
            await pilot.press("tab")
            await pilot.pause()

            # Focus should still be within post_block1 (on Hide button)
            focused = app.focused
            assert post_block1.is_ancestor_of(focused), f"Focus escaped to {focused}"

    @pytest.mark.asyncio
    async def test_up_down_navigate_within_post(self):
        """Up/Down should navigate between focusable elements in post mode."""
        from textual.app import App

        post = make_post()

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            # Enter post mode
            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Start at Comment button
            assert app.focused.id == "btn-comment"

            # Down should move to next focusable
            await pilot.press("down")
            await pilot.pause()
            assert app.focused.id == "btn-like"

            # Up should move back
            await pilot.press("up")
            await pilot.pause()
            assert app.focused.id == "btn-comment"


class TestPostModelOmittedCommentsFields:
    """Tests for omitted comments fields in Post model."""

    def test_post_has_omitted_comments_offset(self):
        """Post should have omitted_comments_offset field."""
        post = make_post(omitted_comments_offset=3)
        assert post.omitted_comments_offset == 3

    def test_post_has_omitted_comment_likes(self):
        """Post should have omitted_comment_likes field."""
        post = make_post(omitted_comment_likes=15)
        assert post.omitted_comment_likes == 15

    def test_post_defaults_omitted_comments_offset_to_zero(self):
        """Post should default omitted_comments_offset to 0."""
        post = make_post()
        assert post.omitted_comments_offset == 0

    def test_post_defaults_omitted_comment_likes_to_zero(self):
        """Post should default omitted_comment_likes to 0."""
        post = make_post()
        assert post.omitted_comment_likes == 0


class TestMoreCommentsButtonPlacement:
    """Tests for correct placement of 'more comments' button based on offset."""

    @pytest.mark.asyncio
    async def test_more_comments_button_at_offset_position(self):
        """More comments button should be placed at omittedCommentsOffset position."""
        from textual.app import App
        from textual.widgets import Button

        # 3 comments, with 10 omitted after first comment (offset=1)
        comments = [make_comment(id=f"c{i}", body=f"Comment {i}") for i in range(3)]
        post = make_post(
            comments=comments,
            omitted_comments=10,
            omitted_comments_offset=1,
            omitted_comment_likes=25,
        )

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            # Get all children in order (comments and buttons)
            from freefood.widgets.post import CommentBlock

            children = list(post_block.query("CommentBlock, #btn-more-comments"))

            # Order should be: Comment0, btn-more-comments, Comment1, Comment2
            assert len(children) == 4
            assert isinstance(children[0], CommentBlock)
            assert children[1].id == "btn-more-comments"
            assert isinstance(children[2], CommentBlock)
            assert isinstance(children[3], CommentBlock)

    @pytest.mark.asyncio
    async def test_more_comments_button_text_includes_likes(self):
        """More comments button should show 'N more comments with M likes'."""
        from textual.app import App
        from textual.widgets import Button

        comments = [make_comment(id=f"c{i}") for i in range(2)]
        post = make_post(
            comments=comments,
            omitted_comments=6,
            omitted_comments_offset=1,
            omitted_comment_likes=8,
        )

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            btn = app.query_one("#btn-more-comments", Button)
            label_text = btn.label.plain
            assert "6 more comments" in label_text
            assert "8 likes" in label_text

    @pytest.mark.asyncio
    async def test_more_comments_button_at_offset_zero(self):
        """More comments button at offset 0 should appear before all comments."""
        from textual.app import App
        from textual.widgets import Button

        comments = [make_comment(id=f"c{i}", body=f"Comment {i}") for i in range(2)]
        post = make_post(
            comments=comments,
            omitted_comments=5,
            omitted_comments_offset=0,
            omitted_comment_likes=10,
        )

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            from freefood.widgets.post import CommentBlock

            children = list(app.query_one(PostBlock).query("CommentBlock, #btn-more-comments"))

            # Order should be: btn-more-comments, Comment0, Comment1
            assert len(children) == 3
            assert children[0].id == "btn-more-comments"
            assert isinstance(children[1], CommentBlock)
            assert isinstance(children[2], CommentBlock)

    @pytest.mark.asyncio
    async def test_more_comments_button_at_end(self):
        """More comments button at offset=len(comments) should appear after all comments."""
        from textual.app import App
        from textual.widgets import Button

        comments = [make_comment(id=f"c{i}", body=f"Comment {i}") for i in range(2)]
        post = make_post(
            comments=comments,
            omitted_comments=5,
            omitted_comments_offset=2,  # offset == len(comments)
            omitted_comment_likes=10,
        )

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            from freefood.widgets.post import CommentBlock

            children = list(app.query_one(PostBlock).query("CommentBlock, #btn-more-comments"))

            # Order should be: Comment0, Comment1, btn-more-comments
            assert len(children) == 3
            assert isinstance(children[0], CommentBlock)
            assert isinstance(children[1], CommentBlock)
            assert children[2].id == "btn-more-comments"

    @pytest.mark.asyncio
    async def test_no_more_comments_button_when_omitted_is_zero(self):
        """No more comments button should appear when omittedComments is 0."""
        from textual.app import App
        from textual.css.query import NoMatches

        # Even with offset set, should not show button when omittedComments=0
        comments = [make_comment(id=f"c{i}") for i in range(3)]
        post = make_post(
            comments=comments,
            omitted_comments=0,
            omitted_comments_offset=1,  # This should be ignored
        )

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            with pytest.raises(NoMatches):
                app.query_one("#btn-more-comments")
