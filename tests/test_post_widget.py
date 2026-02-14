"""Tests for PostBlock widget."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from textual.app import App
from textual.widgets import Button

from freefood.models import Attachment, Comment, Post, User
from freefood.widgets.post import CommentBlock, PostBlock, format_time_ago


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
    direct_recipients: list[User] | None = None,
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
        direct_recipients=direct_recipients or [],
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

    def test_comment_like_requested_message_exists(self):
        """CommentLikeRequested message should be defined and instantiable."""
        comment = make_comment()
        msg = PostBlock.CommentLikeRequested(comment)
        assert msg.comment is comment


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
        assert callable(PostBlock.on_key)


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
        """_body_is_truncated returns False when body is exactly MAX_BODY_LINES."""
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

    def test_format_header_direct_recipients(self):
        """_format_header should include direct recipients."""
        author = make_user(username="alice")
        bob = make_user(id="u2", username="bob")
        carol = make_user(id="u3", username="carol")
        post = make_post(author=author, groups=[], direct_recipients=[bob, carol])
        widget = PostBlock(post)
        header = widget._format_header()
        assert header == "@alice -> @bob, @carol:"


class TestPostBlockFormattingInFeedMode:
    """Tests for formatting behavior in feed mode."""

    @pytest.mark.asyncio
    async def test_direct_recipients_render_as_buttons_in_feed_mode(self):
        """Direct recipients should render as buttons in feed mode."""
        from textual.app import App
        from textual.widgets import Button

        author = make_user(username="alice")
        recipient = make_user(id="u2", username="bob")
        post = make_post(author=author, groups=[], direct_recipients=[recipient])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            button = app.query_one("#user-link-header-user-bob", Button)
            assert button.label.plain == "@bob"

    def test_format_body_short(self):
        """_format_body should return full body when short."""
        post = make_post(body="Short body text")
        widget = PostBlock(post)
        assert widget._format_body() == "Short body text"

    def test_format_body_truncated(self):
        """_format_body should truncate long body and add indicator."""
        lines = [f"Line {i}" for i in range(PostBlock.MAX_BODY_LINES + 10)]
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
        lines = [f"Line {i}" for i in range(PostBlock.MAX_BODY_LINES + 10)]
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

    @pytest.mark.asyncio
    async def test_like_button_not_shown_for_own_post(self):
        """Like button should NOT render for own posts."""
        from textual.app import App
        from textual.css.query import NoMatches

        post = make_post(is_own=True)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            with pytest.raises(NoMatches):
                app.query_one("#btn-like")

    @pytest.mark.asyncio
    async def test_like_button_shown_for_other_post(self):
        """Like button should render for non-own posts."""
        from textual.app import App

        post = make_post(is_own=False)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            btn_like = app.query_one("#btn-like")
            assert btn_like is not None


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
        with patch.object(widget, "refresh"):
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
        mock_button.id = "user-link-header-user-alice"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "post_message") as mock_post_message:
            widget.on_button_pressed(mock_event)

        mock_post_message.assert_called_once()
        msg = mock_post_message.call_args[0][0]
        assert isinstance(msg, PostBlock.UserClicked)
        assert msg.username == "alice"
        assert msg.user_type == "user"

    def test_comment_like_button_emits_message(self):
        """comment-like button press should emit CommentLikeRequested."""
        from unittest.mock import Mock, patch

        from textual.widgets import Button

        comment = make_comment(id="c1")
        post = make_post(comments=[comment])
        widget = PostBlock(post)

        mock_button = Mock(spec=Button)
        mock_button.id = "comment-like-c1"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "post_message") as mock_post_message:
            widget.on_button_pressed(mock_event)

        mock_post_message.assert_called_once()
        msg = mock_post_message.call_args[0][0]
        assert isinstance(msg, PostBlock.CommentLikeRequested)
        assert msg.comment is comment


class TestPostBlockUserLinks:
    """Tests for user link rendering in comments and likes."""

    @pytest.mark.asyncio
    async def test_comment_author_renders_user_link(self):
        """Comment author should render as a user link button."""
        from textual.app import App
        from textual.widgets import Button

        author = make_user(username="bob")
        comment = Comment(
            id="c1",
            body="Nice post",
            author=author,
            created_at=datetime.now(),
            likes=0,
        )
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            app.query_one("#user-link-comment-user-bob", Button)

    @pytest.mark.asyncio
    async def test_likes_render_user_links(self):
        """Likes line should render user link buttons for visible likers."""
        from textual.app import App
        from textual.widgets import Button

        likers = [
            make_user(id="u1", username="bob"),
            make_user(id="u2", username="carol"),
        ]
        post = make_post(likes=likers)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            app.query_one("#user-link-like-user-bob", Button)
            app.query_one("#user-link-like-user-carol", Button)


class TestPostBlockLayout:
    """Tests for non-expanding layout containers."""

    @pytest.mark.asyncio
    async def test_post_header_uses_horizontal_group(self):
        """Post header should use a non-expanding horizontal container."""
        from textual.app import App
        from textual.containers import HorizontalGroup

        post = make_post()

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            app.query_one("#post-header", HorizontalGroup)

    @pytest.mark.asyncio
    async def test_post_likes_uses_horizontal_group(self):
        """Post likes should use a non-expanding horizontal container."""
        from textual.app import App
        from textual.containers import HorizontalGroup

        likers = [make_user(username="bob")]
        post = make_post(likes=likers)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            app.query_one("#post-likes", HorizontalGroup)

    @pytest.mark.asyncio
    async def test_comment_uses_group_containers(self):
        """Comment block should use non-expanding containers."""
        from textual.app import App
        from textual.containers import HorizontalGroup, VerticalGroup

        author = make_user(username="bob")
        comment = Comment(
            id="c1",
            body="Nice post",
            author=author,
            created_at=datetime.now(),
            likes=0,
        )
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            app.query_one("#comment-container", VerticalGroup)
            app.query_one("#comment-meta", HorizontalGroup)


class TestCommentAuthorVisibility:
    """Tests for comment author placement."""

    @pytest.mark.asyncio
    async def test_comment_author_not_pushed_off_screen(self):
        """Comment author should appear near the comment prefix."""
        from textual.app import App
        from textual.containers import HorizontalGroup
        from textual.widgets import Button

        author = make_user(username="bob")
        comment = Comment(
            id="c1",
            body="Nice post",
            author=author,
            created_at=datetime.now(),
            likes=0,
        )
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            meta = app.query_one("#comment-meta", HorizontalGroup)
            button = app.query_one("#user-link-comment-user-bob", Button)
            assert button.region.x - meta.region.x < 10


class TestLikeAuthorVisibility:
    """Tests for like user placement."""

    @pytest.mark.asyncio
    async def test_like_user_not_pushed_off_screen(self):
        """Like users should appear near the likes prefix."""
        from textual.app import App
        from textual.containers import HorizontalGroup
        from textual.widgets import Button

        likers = [make_user(username="bob")]
        post = make_post(likes=likers)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            likes = app.query_one("#post-likes", HorizontalGroup)
            button = app.query_one("#user-link-like-user-bob", Button)
            assert button.region.x - likes.region.x < 10


class TestUserLinkSpacing:
    """Tests for user link spacing."""

    @pytest.mark.asyncio
    async def test_user_link_not_overly_wide(self):
        """User link button should not add extra padding."""
        from textual.app import App
        from textual.widgets import Button

        post = make_post()

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            button = app.query_one("#user-link-header-user-alice", Button)
            assert button.region.width <= len("@alice") + 2

    @pytest.mark.asyncio
    async def test_direct_recipient_link_is_visible(self):
        """Direct recipient link should render in feed mode."""
        from textual.app import App
        from textual.widgets import Button

        author = make_user(username="alice")
        recipient = make_user(id="u2", username="bob")
        post = make_post(author=author, groups=[], direct_recipients=[recipient])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            button = app.query_one("#user-link-header-user-bob", Button)
            assert button.region.width > 0


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

    @pytest.mark.asyncio
    async def test_hide_button_hidden_when_show_hide_button_false(self):
        """Hide button should not render when show_hide_button=False."""
        from textual.app import App
        from textual.css.query import NoMatches

        post = make_post(is_hidden=False)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post, show_hide_button=False)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            with pytest.raises(NoMatches):
                app.query_one("#btn-hide")

    @pytest.mark.asyncio
    async def test_hide_button_shown_when_show_hide_button_true(self):
        """Hide button should render when show_hide_button=True."""
        from textual.app import App

        post = make_post(is_hidden=False)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post, show_hide_button=True)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            btn_hide = app.query_one("#btn-hide")
            assert btn_hide is not None


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


class TestCommentLikeButton:
    """Tests for comment like button rendering and focus behavior."""

    @pytest.mark.asyncio
    async def test_comment_like_button_rendered(self):
        """Comment like button should render in post mode."""
        from textual.app import App

        comment = make_comment(id="c1")
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            block = app.query_one(PostBlock)
            block.action_enter_post_mode()
            await pilot.pause()

            btn = app.query_one("#comment-like-c1", Button)
            assert "Like" in btn.label.plain

    @pytest.mark.asyncio
    async def test_comment_unlike_button_when_liked(self):
        """Comment like button should show Unlike when comment is liked."""
        from textual.app import App

        comment = make_comment(id="c1")
        comment.is_liked = True
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            block = app.query_one(PostBlock)
            block.action_enter_post_mode()
            await pilot.pause()

            btn = app.query_one("#comment-like-c1", Button)
            assert "Unlike" in btn.label.plain

    @pytest.mark.asyncio
    async def test_comment_like_button_not_focusable_outside_post_mode(self):
        """Comment like button should not be focusable outside post mode."""
        from textual.app import App

        comment = make_comment(id="c1")
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            btn = app.query_one("#comment-like-c1", Button)
            assert btn.can_focus is False

    @pytest.mark.asyncio
    async def test_comment_like_button_is_single_line(self):
        """Comment like button should match post-like button height."""
        from textual.app import App

        comment = make_comment(id="c1")
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            block = app.query_one(PostBlock)
            block.action_enter_post_mode()
            await pilot.pause()

            comment_btn = app.query_one("#comment-like-c1", Button)
            post_btn = app.query_one("#btn-like", Button)
            assert comment_btn.region.height == post_btn.region.height

    @pytest.mark.asyncio
    async def test_comment_edit_delete_buttons_are_single_line(self):
        """Own-comment edit/delete should match post-like button height."""
        from textual.app import App

        comment = make_comment(id="c1")
        comment.is_own = True
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            block = app.query_one(PostBlock)
            block.action_enter_post_mode()
            await pilot.pause()

            btn_edit = app.query_one("#comment-edit-c1", Button)
            btn_delete = app.query_one("#comment-delete-c1", Button)
            post_btn = app.query_one("#btn-like", Button)
            assert btn_edit.region.height == post_btn.region.height
            assert btn_delete.region.height == post_btn.region.height

    @pytest.mark.asyncio
    async def test_comment_like_button_not_shown_for_own_comment(self):
        """Own comments should not render a like button."""
        from textual.app import App
        from textual.css.query import NoMatches

        comment = make_comment(id="c1")
        comment.is_own = True
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            with pytest.raises(NoMatches):
                app.query_one("#comment-like-c1", Button)

    @pytest.mark.asyncio
    async def test_comment_like_button_shown_for_other_comment(self):
        """Non-own comments should render a like button."""
        from textual.app import App

        comment = make_comment(id="c1")
        comment.is_own = False
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            btn = app.query_one("#comment-like-c1", Button)
            assert btn is not None

    @pytest.mark.asyncio
    async def test_comment_edit_and_like_mutually_exclusive(self):
        """Own comment shows edit/delete; non-own shows like."""
        from textual.app import App
        from textual.css.query import NoMatches

        own_comment = make_comment(id="c1")
        own_comment.is_own = True
        own_post = make_post(comments=[own_comment])

        class OwnApp(App):
            def compose(self):
                yield PostBlock(own_post)

        async with OwnApp().run_test() as pilot:
            app = pilot.app
            app.query_one("#comment-edit-c1", Button)
            with pytest.raises(NoMatches):
                app.query_one("#comment-like-c1", Button)

        other_comment = make_comment(id="c2")
        other_comment.is_own = False
        other_post = make_post(comments=[other_comment])

        class OtherApp(App):
            def compose(self):
                yield PostBlock(other_post)

        async with OtherApp().run_test() as pilot:
            app = pilot.app
            app.query_one("#comment-like-c2", Button)
            with pytest.raises(NoMatches):
                app.query_one("#comment-edit-c2", Button)


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
                assert cw.can_focus is False, (
                    "Comment should not be focusable outside post mode"
                )

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
            assert isinstance(focused, CommentBlock), (
                f"Expected CommentBlock, got {type(focused)}"
            )


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
            assert more_btn.can_focus is True, (
                "More comments button should be focusable"
            )

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
            assert more_btn.can_focus is False, (
                "More comments button should not be focusable outside post mode"
            )

    @pytest.mark.asyncio
    async def test_can_navigate_to_more_comments_button(self):
        """Should be able to navigate to more comments button in post mode."""
        from textual.app import App

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
            assert focused.id == "btn-more-comments", (
                f"Expected btn-more-comments, got {focused.id}"
            )

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
            assert more_btn.can_focus is True, (
                "More comments button should be focusable"
            )


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

    @pytest.mark.asyncio
    async def test_up_from_comment_focuses_header_user_link(self):
        """Up from Comment should focus the post author user link."""
        from textual.app import App
        from textual.widgets import Button

        post = make_post(author=make_user(username="alice"))

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

            # Up should move to the author user link
            await pilot.press("up")
            await pilot.pause()

            focused = app.focused
            assert isinstance(focused, Button)
            assert focused.id == "user-link-header-user-alice"

    @pytest.mark.asyncio
    async def test_liker_user_links_focusable_in_post_mode(self):
        """Liker user links should be focusable in post mode."""
        from textual.app import App
        from textual.widgets import Button

        likers = [
            make_user(id="u1", username="bob"),
            make_user(id="u2", username="carol"),
        ]
        post = make_post(likes=likers)

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

            bob_link = app.query_one("#user-link-like-user-bob", Button)
            carol_link = app.query_one("#user-link-like-user-carol", Button)

            assert bob_link.can_focus is True
            assert carol_link.can_focus is True

    @pytest.mark.asyncio
    async def test_tab_from_comment_focuses_comment_author(self):
        """Tab from a comment should focus its author user link."""
        from textual.app import App
        from textual.widgets import Button

        from freefood.widgets.post import CommentBlock

        author = make_user(username="bob")
        comment = Comment(
            id="c1",
            body="Nice post",
            author=author,
            created_at=datetime.now(),
            likes=0,
        )
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

            comment_block = app.query_one(CommentBlock)
            app.set_focus(comment_block)
            await pilot.pause()

            await pilot.press("tab")
            await pilot.pause()

            focused = app.focused
            assert isinstance(focused, Button)
            assert focused.id == "user-link-comment-user-bob"


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

            children = list(
                app.query_one(PostBlock).query("CommentBlock, #btn-more-comments")
            )

            # Order should be: btn-more-comments, Comment0, Comment1
            assert len(children) == 3
            assert children[0].id == "btn-more-comments"
            assert isinstance(children[1], CommentBlock)
            assert isinstance(children[2], CommentBlock)

    @pytest.mark.asyncio
    async def test_more_comments_button_at_end(self):
        """More comments button at offset=len(comments) appears after all comments."""
        from textual.app import App

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

            children = list(
                app.query_one(PostBlock).query("CommentBlock, #btn-more-comments")
            )

            # Order should be: Comment0, Comment1, btn-more-comments
            assert len(children) == 3
            assert isinstance(children[0], CommentBlock)
            assert isinstance(children[1], CommentBlock)
            assert children[2].id == "btn-more-comments"

    @pytest.mark.asyncio
    async def test_no_more_comments_button_when_omitted_is_zero(self):
        """No more comments button should appear when omittedComments is 0."""
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


# =========================================================================
# New coverage tests for uncovered lines
# =========================================================================


class TestCommentBlockTruncation:
    """Tests for CommentBlock body truncation (line 95)."""

    def test_comment_body_truncated_when_exceeding_max_lines(self):
        """CommentBlock should truncate body exceeding MAX_COMMENT_LINES."""
        lines = [f"Line {i}" for i in range(CommentBlock.MAX_COMMENT_LINES + 5)]
        body = "\n".join(lines)
        comment = make_comment(body=body)
        block = CommentBlock(comment)
        formatted = block._format_body()
        assert "[show more...]" in formatted
        output_lines = formatted.split("\n")
        assert len(output_lines) == CommentBlock.MAX_COMMENT_LINES + 1


class TestCommentBlockHighlighting:
    """Tests for CommentBlock with highlight terms (lines 100, 116)."""

    def test_comment_format_body_with_highlight_terms(self):
        """CommentBlock._format_body with highlight_terms should use highlight_text."""
        comment = make_comment(body="Hello world test")
        block = CommentBlock(comment, highlight_terms=["world"])
        formatted = block._format_body()
        # highlight_text uses Rich markup
        assert "[reverse]" in formatted

    @pytest.mark.asyncio
    async def test_comment_likes_escaped_with_highlight_terms(self):
        """CommentBlock with highlight_terms should escape likes_str."""
        comment = make_comment(body="Hello", likes=3)
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post, highlight_terms=["Hello"])

        async with TestApp().run_test() as pilot:
            app = pilot.app
            # Should render without error - the likes_str is escaped
            comment_blocks = list(app.query(CommentBlock))
            assert len(comment_blocks) == 1


class TestCommentBlockNullAuthor:
    """Tests for CommentBlock with None author (line 138)."""

    @pytest.mark.asyncio
    async def test_comment_null_author_renders_unknown(self):
        """CommentBlock should show @unknown when author is None."""
        from textual.widgets import Static

        comment = Comment(
            id="c_null",
            body="Anonymous comment",
            author=None,
            created_at=datetime.now(),
            likes=0,
        )
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            comment_block = app.query_one(CommentBlock)
            # Should have a Static with @unknown
            statics = list(comment_block.query(Static))
            unknown_statics = [s for s in statics if "@unknown" in s.content]
            assert len(unknown_statics) == 1


class TestPostBlockNullAuthor:
    """Tests for PostBlock with None author (line 390)."""

    @pytest.mark.asyncio
    async def test_post_null_author_renders_unknown(self):
        """PostBlock should show @unknown when author is None."""
        from textual.widgets import Static

        post = make_post()
        post.author = None

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            from textual.containers import HorizontalGroup

            header = app.query_one("#post-header", HorizontalGroup)
            statics = list(header.query(Static))
            unknown_statics = [s for s in statics if "@unknown" in s.content]
            assert len(unknown_statics) == 1


class TestPostBlockMultipleDirectRecipients:
    """Tests for multiple direct recipients separator (line 396)."""

    @pytest.mark.asyncio
    async def test_multiple_direct_recipients_separator(self):
        """Multiple direct recipients should be separated by commas."""
        from textual.widgets import Static

        author = make_user(username="alice")
        bob = make_user(id="u2", username="bob")
        carol = make_user(id="u3", username="carol")
        post = make_post(author=author, groups=[], direct_recipients=[bob, carol])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            # Both recipients should have buttons
            app.query_one("#user-link-header-user-bob", Button)
            app.query_one("#user-link-header-user-carol", Button)
            # Separator statics should exist
            from textual.containers import HorizontalGroup

            header = app.query_one("#post-header", HorizontalGroup)
            statics = list(header.query(Static))
            comma_statics = [s for s in statics if ", " in s.content]
            assert len(comma_statics) >= 1


class TestPostBlockMultipleGroups:
    """Tests for multiple groups separator (line 411)."""

    @pytest.mark.asyncio
    async def test_multiple_groups_separator(self):
        """Multiple groups should be separated by commas."""
        author = make_user(username="alice")
        group1 = make_user(id="g1", username="news", user_type="group")
        group2 = make_user(id="g2", username="tech", user_type="group")
        post = make_post(author=author, groups=[group1, group2])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            app.query_one("#user-link-header-group-news", Button)
            app.query_one("#user-link-header-group-tech", Button)


class TestPostBlockAttachmentFilenameEdgeCases:
    """Tests for truncate_filename edge cases (line 552)."""

    @pytest.mark.asyncio
    async def test_attachment_long_suffix_truncation(self):
        """Attachment with very long suffix should truncate correctly."""
        # Create a filename where stem_len would be <= 0
        # max_len=20, suffix=".verylongsuffix" (15 chars), stem_len = 20-15-3 = 2
        att = Attachment(
            id="att1",
            file_name="ab.verylongsuffix",
            file_size=1024,
            media_type="application/octet-stream",
            url="https://example.com/file",
        )
        post = make_post()
        post.attachments = [att]

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            btn = app.query_one(f"#att-{att.id}", Button)
            assert btn is not None

    @pytest.mark.asyncio
    async def test_attachment_extremely_long_suffix_truncation(self):
        """Attachment where stem_len <= 0 should use fallback truncation."""
        # max_len=20, suffix len > 17 means stem_len <= 0
        att = Attachment(
            id="att2",
            file_name="x.areallyreallyreallylongsuffix",
            file_size=1024,
            media_type="application/pdf",
            url="https://example.com/file2",
        )
        post = make_post()
        post.attachments = [att]

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            btn = app.query_one(f"#att-{att.id}", Button)
            assert btn is not None

    @pytest.mark.asyncio
    async def test_attachment_media_type_icons(self):
        """Different media types should get different icons."""
        attachments = [
            Attachment(
                id="att_img",
                file_name="photo.jpg",
                file_size=1024,
                media_type="image/jpeg",
                url="https://example.com/img",
            ),
            Attachment(
                id="att_vid",
                file_name="video.mp4",
                file_size=2048,
                media_type="video/mp4",
                url="https://example.com/vid",
            ),
            Attachment(
                id="att_audio",
                file_name="song.mp3",
                file_size=512,
                media_type="audio/mpeg",
                url="https://example.com/audio",
            ),
            Attachment(
                id="att_text",
                file_name="doc.txt",
                file_size=256,
                media_type="text/plain",
                url="https://example.com/text",
            ),
            Attachment(
                id="att_other",
                file_name="data.bin",
                file_size=128,
                media_type="application/octet-stream",
                url="https://example.com/bin",
            ),
        ]
        post = make_post()
        post.attachments = attachments

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            for att in attachments:
                btn = app.query_one(f"#att-{att.id}", Button)
                assert btn is not None


class TestPostBlockMoreThanThreeLikesRendering:
    """Tests for >3 likes rendering (lines 644-645)."""

    @pytest.mark.asyncio
    async def test_more_than_three_likes_shows_others_count(self):
        """More than 3 likes should show 'and N others liked this'."""
        from textual.widgets import Static

        likers = [make_user(id=f"u{i}", username=f"user{i}") for i in range(5)]
        post = make_post(likes=likers, omitted_likes=10)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            from textual.containers import HorizontalGroup

            likes_group = app.query_one("#post-likes", HorizontalGroup)
            statics = list(likes_group.query(Static))
            text = " ".join(s.content for s in statics)
            assert "others liked this" in text


class TestPostBlockButtonPressHandlers:
    """Tests for various on_button_pressed branches."""

    def test_btn_more_comments_sets_expanded(self):
        """btn-more-comments press should set comments_expanded and emit."""
        post = make_post(omitted_comments=5)
        widget = PostBlock(post)

        mock_button = Mock(spec=Button)
        mock_button.id = "btn-more-comments"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "post_message") as mock_post_message:
            widget.on_button_pressed(mock_event)

        assert widget.comments_expanded is True
        msg = mock_post_message.call_args[0][0]
        assert isinstance(msg, PostBlock.ExpandComments)

    def test_btn_comment_calls_show_comment_compose(self):
        """btn-comment press should call _show_comment_compose."""
        post = make_post()
        widget = PostBlock(post)

        mock_button = Mock(spec=Button)
        mock_button.id = "btn-comment"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "_show_comment_compose") as mock_show:
            widget.on_button_pressed(mock_event)

        mock_show.assert_called_once()

    def test_btn_edit_calls_start_editing_post(self):
        """btn-edit press should call _start_editing_post."""
        post = make_post(is_own=True)
        widget = PostBlock(post)

        mock_button = Mock(spec=Button)
        mock_button.id = "btn-edit"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "_start_editing_post") as mock_edit:
            widget.on_button_pressed(mock_event)

        mock_edit.assert_called_once()

    def test_btn_cancel_edit_calls_cancel_editing_post(self):
        """btn-cancel-edit press should call _cancel_editing_post."""
        post = make_post(is_own=True)
        widget = PostBlock(post)

        mock_button = Mock(spec=Button)
        mock_button.id = "btn-cancel-edit"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "_cancel_editing_post") as mock_cancel:
            widget.on_button_pressed(mock_event)

        mock_cancel.assert_called_once()

    def test_btn_save_edit_calls_save_editing_post(self):
        """btn-save-edit press should call _save_editing_post."""
        post = make_post(is_own=True)
        widget = PostBlock(post)

        mock_button = Mock(spec=Button)
        mock_button.id = "btn-save-edit"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "_save_editing_post") as mock_save:
            widget.on_button_pressed(mock_event)

        mock_save.assert_called_once()

    def test_btn_delete_calls_start_delete_confirmation(self):
        """btn-delete press should call _start_delete_confirmation."""
        post = make_post(is_own=True)
        widget = PostBlock(post)

        mock_button = Mock(spec=Button)
        mock_button.id = "btn-delete"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "_start_delete_confirmation") as mock_del:
            widget.on_button_pressed(mock_event)

        mock_del.assert_called_once()

    def test_btn_cancel_delete_calls_cancel_delete_confirmation(self):
        """btn-cancel-delete press should call _cancel_delete_confirmation."""
        post = make_post(is_own=True)
        widget = PostBlock(post)

        mock_button = Mock(spec=Button)
        mock_button.id = "btn-cancel-delete"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "_cancel_delete_confirmation") as mock_cd:
            widget.on_button_pressed(mock_event)

        mock_cd.assert_called_once()

    def test_btn_confirm_delete_calls_confirm_delete(self):
        """btn-confirm-delete press should call _confirm_delete."""
        post = make_post(is_own=True)
        widget = PostBlock(post)

        mock_button = Mock(spec=Button)
        mock_button.id = "btn-confirm-delete"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "_confirm_delete") as mock_confirm:
            widget.on_button_pressed(mock_event)

        mock_confirm.assert_called_once()

    def test_comment_edit_button_calls_start_editing_comment(self):
        """comment-edit-{id} press should call _start_editing_comment."""
        comment = make_comment(id="c42")
        post = make_post(comments=[comment])
        widget = PostBlock(post)

        mock_button = Mock(spec=Button)
        mock_button.id = "comment-edit-c42"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "_start_editing_comment") as mock_edit:
            widget.on_button_pressed(mock_event)

        mock_edit.assert_called_once_with("c42")

    def test_btn_cancel_comment_edit(self):
        """btn-cancel-comment-edit press should call _cancel_editing_comment."""
        post = make_post()
        widget = PostBlock(post)

        mock_button = Mock(spec=Button)
        mock_button.id = "btn-cancel-comment-edit"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "_cancel_editing_comment") as mock_cancel:
            widget.on_button_pressed(mock_event)

        mock_cancel.assert_called_once()

    def test_btn_save_comment_edit(self):
        """btn-save-comment-edit press should call _save_editing_comment."""
        post = make_post()
        widget = PostBlock(post)

        mock_button = Mock(spec=Button)
        mock_button.id = "btn-save-comment-edit"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "_save_editing_comment") as mock_save:
            widget.on_button_pressed(mock_event)

        mock_save.assert_called_once()

    def test_comment_delete_button(self):
        """comment-delete-{id} press should call _start_comment_delete_confirmation."""
        post = make_post()
        widget = PostBlock(post)

        mock_button = Mock(spec=Button)
        mock_button.id = "comment-delete-c99"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "_start_comment_delete_confirmation") as mock_del:
            widget.on_button_pressed(mock_event)

        mock_del.assert_called_once_with("c99")

    def test_comment_confirm_delete_button(self):
        """comment-confirm-delete-{id} press should call _confirm_delete_comment."""
        post = make_post()
        widget = PostBlock(post)

        mock_button = Mock(spec=Button)
        mock_button.id = "comment-confirm-delete-c99"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "_confirm_delete_comment") as mock_cd:
            widget.on_button_pressed(mock_event)

        mock_cd.assert_called_once_with("c99")

    def test_comment_cancel_delete_button(self):
        """comment-cancel-delete should call cancel confirmation."""
        post = make_post()
        widget = PostBlock(post)

        mock_button = Mock(spec=Button)
        mock_button.id = "comment-cancel-delete-c99"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "_cancel_comment_delete_confirmation") as mock_cancel:
            widget.on_button_pressed(mock_event)

        mock_cancel.assert_called_once_with("c99")

    def test_attachment_button_emits_attachment_opened(self):
        """att-{id} press should emit AttachmentOpened."""
        att = Attachment(
            id="att99",
            file_name="file.txt",
            file_size=100,
            media_type="text/plain",
            url="https://example.com/file",
        )
        post = make_post()
        post.attachments = [att]
        widget = PostBlock(post)

        mock_button = Mock(spec=Button)
        mock_button.id = "att-att99"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "post_message") as mock_pm:
            widget.on_button_pressed(mock_event)

        msg = mock_pm.call_args[0][0]
        assert isinstance(msg, PostBlock.AttachmentOpened)
        assert msg.attachment is att

    def test_attachment_button_unknown_id_no_message(self):
        """att-{id} with nonexistent attachment id should not emit."""
        post = make_post()
        post.attachments = []
        widget = PostBlock(post)

        mock_button = Mock(spec=Button)
        mock_button.id = "att-nonexistent"
        mock_event = Mock(spec=Button.Pressed)
        mock_event.button = mock_button

        with patch.object(widget, "post_message") as mock_pm:
            widget.on_button_pressed(mock_event)

        mock_pm.assert_not_called()


class TestPostBlockEditingPost:
    """Tests for post editing flow."""

    @pytest.mark.asyncio
    async def test_edit_post_shows_textarea(self):
        """Editing post should show textarea with post body."""
        from textual.widgets import TextArea

        post = make_post(body="Original body", is_own=True)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            # Enter post mode and click Edit
            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            edit_btn = app.query_one("#btn-edit", Button)
            edit_btn.press()
            await pilot.pause()

            assert post_block.editing_post is True
            textarea = app.query_one("#edit-post-body", TextArea)
            assert textarea.text == "Original body"

    @pytest.mark.asyncio
    async def test_cancel_edit_post_restores_view(self):
        """Cancelling edit should restore normal view."""
        post = make_post(body="Original body", is_own=True)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Start editing
            edit_btn = app.query_one("#btn-edit", Button)
            edit_btn.press()
            await pilot.pause()
            assert post_block.editing_post is True

            # Cancel editing
            cancel_btn = app.query_one("#btn-cancel-edit", Button)
            cancel_btn.press()
            await pilot.pause()
            assert post_block.editing_post is False

    @pytest.mark.asyncio
    async def test_save_edit_post_emits_message(self):
        """Saving edited post should emit EditPostRequested."""
        from textual.widgets import TextArea

        messages = []
        post = make_post(body="Original body", is_own=True)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

            def on_post_block_edit_post_requested(self, event):
                messages.append(event)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            edit_btn = app.query_one("#btn-edit", Button)
            edit_btn.press()
            await pilot.pause()

            textarea = app.query_one("#edit-post-body", TextArea)
            textarea.text = "Updated body"
            await pilot.pause()

            save_btn = app.query_one("#btn-save-edit", Button)
            save_btn.press()
            await pilot.pause()

            assert len(messages) == 1
            assert messages[0].new_body == "Updated body"

    @pytest.mark.asyncio
    async def test_save_edit_post_empty_body_no_message(self):
        """Saving with empty body should not emit."""
        from textual.widgets import TextArea

        messages = []
        post = make_post(body="Original body", is_own=True)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

            def on_post_block_edit_post_requested(self, event):
                messages.append(event)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            edit_btn = app.query_one("#btn-edit", Button)
            edit_btn.press()
            await pilot.pause()

            textarea = app.query_one("#edit-post-body", TextArea)
            textarea.text = "   "
            await pilot.pause()

            save_btn = app.query_one("#btn-save-edit", Button)
            save_btn.press()
            await pilot.pause()

            assert len(messages) == 0


class TestPostBlockDeleteFlow:
    """Tests for post delete confirmation flow."""

    @pytest.mark.asyncio
    async def test_delete_shows_confirmation(self):
        """Clicking Delete should show Confirm Delete and Cancel buttons."""
        post = make_post(is_own=True)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            delete_btn = app.query_one("#btn-delete", Button)
            delete_btn.press()
            await pilot.pause()

            assert post_block.confirming_delete is True
            app.query_one("#btn-confirm-delete", Button)
            app.query_one("#btn-cancel-delete", Button)

    @pytest.mark.asyncio
    async def test_cancel_delete_hides_confirmation(self):
        """Clicking Cancel in delete confirmation should hide it."""
        post = make_post(is_own=True)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            delete_btn = app.query_one("#btn-delete", Button)
            delete_btn.press()
            await pilot.pause()

            cancel_btn = app.query_one("#btn-cancel-delete", Button)
            cancel_btn.press()
            await pilot.pause()

            assert post_block.confirming_delete is False

    @pytest.mark.asyncio
    async def test_confirm_delete_emits_message(self):
        """Clicking Confirm Delete should emit DeletePostRequested."""
        messages = []
        post = make_post(is_own=True)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

            def on_post_block_delete_post_requested(self, event):
                messages.append(event)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            delete_btn = app.query_one("#btn-delete", Button)
            delete_btn.press()
            await pilot.pause()

            confirm_btn = app.query_one("#btn-confirm-delete", Button)
            confirm_btn.press()
            await pilot.pause()

            assert len(messages) == 1
            assert isinstance(messages[0], PostBlock.DeletePostRequested)


class TestPostBlockCommentEditing:
    """Tests for comment editing flow."""

    @pytest.mark.asyncio
    async def test_comment_edit_shows_textarea(self):
        """Clicking Edit on own comment should show textarea."""
        from textual.widgets import TextArea

        comment = Comment(
            id="c_edit",
            body="My comment",
            author=make_user(username="me"),
            created_at=datetime.now(),
            likes=0,
            is_own=True,
        )
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            edit_btn = app.query_one("#comment-edit-c_edit", Button)
            edit_btn.press()
            await pilot.pause()
            # Wait for timer
            await pilot.pause(delay=0.1)

            textarea = app.query_one("#edit-comment-body", TextArea)
            assert textarea.text == "My comment"

    @pytest.mark.asyncio
    async def test_comment_cancel_edit_restores_view(self):
        """Cancelling comment edit should restore normal comment view."""
        comment = Comment(
            id="c_edit2",
            body="My comment",
            author=make_user(username="me"),
            created_at=datetime.now(),
            likes=0,
            is_own=True,
        )
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Start editing
            edit_btn = app.query_one("#comment-edit-c_edit2", Button)
            edit_btn.press()
            await pilot.pause()

            # Cancel editing
            cancel_btn = app.query_one("#btn-cancel-comment-edit", Button)
            cancel_btn.press()
            await pilot.pause()
            # Wait for timer
            await pilot.pause()

            # Comment block should not be editing anymore
            comment_block = app.query_one(CommentBlock)
            assert comment_block.editing is False

    @pytest.mark.asyncio
    async def test_comment_save_edit_emits_message(self):
        """Saving comment edit should emit EditCommentRequested."""
        from textual.widgets import TextArea

        messages = []
        comment = Comment(
            id="c_save",
            body="Old text",
            author=make_user(username="me"),
            created_at=datetime.now(),
            likes=0,
            is_own=True,
        )
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

            def on_post_block_edit_comment_requested(self, event):
                messages.append(event)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            edit_btn = app.query_one("#comment-edit-c_save", Button)
            edit_btn.press()
            await pilot.pause()
            await pilot.pause(delay=0.1)

            textarea = app.query_one("#edit-comment-body", TextArea)
            textarea.text = "New text"
            await pilot.pause()

            save_btn = app.query_one("#btn-save-comment-edit", Button)
            save_btn.press()
            await pilot.pause()

            assert len(messages) == 1
            assert messages[0].new_body == "New text"


class TestPostBlockCommentDeleteFlow:
    """Tests for comment delete confirmation flow."""

    @pytest.mark.asyncio
    async def test_comment_delete_shows_confirmation(self):
        """Clicking Delete on own comment should show confirmation."""
        comment = Comment(
            id="c_del",
            body="My comment",
            author=make_user(username="me"),
            created_at=datetime.now(),
            likes=0,
            is_own=True,
        )
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            delete_btn = app.query_one("#comment-delete-c_del", Button)
            delete_btn.press()
            await pilot.pause()

            comment_block = app.query_one(CommentBlock)
            assert comment_block.confirming_delete is True
            app.query_one("#comment-confirm-delete-c_del", Button)
            app.query_one("#comment-cancel-delete-c_del", Button)

    @pytest.mark.asyncio
    async def test_comment_cancel_delete_hides_confirmation(self):
        """Cancelling comment delete should hide confirmation buttons."""
        comment = Comment(
            id="c_cdel",
            body="My comment",
            author=make_user(username="me"),
            created_at=datetime.now(),
            likes=0,
            is_own=True,
        )
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            delete_btn = app.query_one("#comment-delete-c_cdel", Button)
            delete_btn.press()
            await pilot.pause()

            cancel_btn = app.query_one("#comment-cancel-delete-c_cdel", Button)
            cancel_btn.press()
            await pilot.pause()

            comment_block = app.query_one(CommentBlock)
            assert comment_block.confirming_delete is False

    @pytest.mark.asyncio
    async def test_comment_confirm_delete_emits_message(self):
        """Confirming comment delete should emit DeleteCommentRequested."""
        messages = []
        comment = Comment(
            id="c_cfdel",
            body="My comment",
            author=make_user(username="me"),
            created_at=datetime.now(),
            likes=0,
            is_own=True,
        )
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

            def on_post_block_delete_comment_requested(self, event):
                messages.append(event)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            delete_btn = app.query_one("#comment-delete-c_cfdel", Button)
            delete_btn.press()
            await pilot.pause()

            confirm_btn = app.query_one("#comment-confirm-delete-c_cfdel", Button)
            confirm_btn.press()
            await pilot.pause()

            assert len(messages) == 1
            assert isinstance(messages[0], PostBlock.DeleteCommentRequested)
            assert messages[0].comment.id == "c_cfdel"


class TestPostBlockFocusCommentAt:
    """Tests for focus_comment_at (line 835)."""

    @pytest.mark.asyncio
    async def test_focus_comment_at_no_comments_returns_false(self):
        """focus_comment_at with no comments should return False."""
        post = make_post(comments=[])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)
            result = post_block.focus_comment_at(0)
            assert result is False

    @pytest.mark.asyncio
    async def test_focus_comment_at_valid_index(self):
        """focus_comment_at with valid index should focus the comment."""
        comments = [
            make_comment(id="c1", body="First"),
            make_comment(id="c2", body="Second"),
        ]
        post = make_post(comments=comments)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)
            # Enter post mode so comments are focusable
            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            result = post_block.focus_comment_at(1)
            assert result is True


class TestPostBlockCommentCompose:
    """Tests for comment compose (line 853)."""

    @pytest.mark.asyncio
    async def test_comment_compose_cancelled(self):
        """on_comment_compose_cancelled should hide the compose widget."""
        from freefood.widgets.comment_compose import CommentCompose

        post = make_post()

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Click Comment button to show compose
            comment_btn = app.query_one("#btn-comment", Button)
            comment_btn.press()
            await pilot.pause()

            # Should have a CommentCompose widget
            compose_widgets = list(post_block.query(CommentCompose))
            assert len(compose_widgets) == 1

            # Now cancel it
            cancel_btn = app.query_one("#comment-cancel", Button)
            cancel_btn.press()
            await pilot.pause()

            # CommentCompose should be gone
            compose_widgets = list(post_block.query(CommentCompose))
            assert len(compose_widgets) == 0


class TestPostBlockFocusFirstButtonFallback:
    """Tests for _focus_first_button fallback (lines 870-873)."""

    @pytest.mark.asyncio
    async def test_focus_first_button_when_editing(self):
        """_focus_first_button should fallback when btn-comment doesn't exist."""
        post = make_post(is_own=True)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            # Enter editing mode first (removes btn-comment)
            post_block.editing_post = True
            post_block.post_mode = True
            post_block.refresh(recompose=True)
            await pilot.pause()

            # Should focus Cancel or Save button (fallback path)
            post_block._focus_first_button()
            await pilot.pause()
            # Focus should be on one of the edit action buttons
            focused = app.focused
            assert focused is not None


class TestPostBlockOnKeyEdgeCases:
    """Tests for on_key edge cases (lines 912, 915, 947)."""

    @pytest.mark.asyncio
    async def test_on_key_escape_in_edit_mode(self):
        """Escape in editing mode should cancel edit."""
        post = make_post(is_own=True)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            edit_btn = app.query_one("#btn-edit", Button)
            edit_btn.press()
            await pilot.pause()

            assert post_block.editing_post is True

            # Press escape
            await pilot.press("escape")
            await pilot.pause()
            assert post_block.editing_post is False

    @pytest.mark.asyncio
    async def test_on_key_ctrl_enter_in_edit_mode(self):
        """Ctrl+Enter in editing mode should save edit."""
        from textual.widgets import TextArea

        messages = []
        post = make_post(body="Old body", is_own=True)

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

            def on_post_block_edit_post_requested(self, event):
                messages.append(event)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            edit_btn = app.query_one("#btn-edit", Button)
            edit_btn.press()
            await pilot.pause()

            textarea = app.query_one("#edit-post-body", TextArea)
            textarea.text = "New body"
            await pilot.pause()

            await pilot.press("ctrl+enter")
            await pilot.pause()

            assert len(messages) == 1
            assert messages[0].new_body == "New body"

    @pytest.mark.asyncio
    async def test_on_key_escape_in_comment_edit_mode(self):
        """Escape while editing comment should cancel comment edit."""
        comment = Comment(
            id="c_esc",
            body="My comment",
            author=make_user(username="me"),
            created_at=datetime.now(),
            likes=0,
            is_own=True,
        )
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Start editing comment
            edit_btn = app.query_one("#comment-edit-c_esc", Button)
            edit_btn.press()
            await pilot.pause()

            # Press escape to cancel
            await pilot.press("escape")
            await pilot.pause()
            # Wait for timer
            await pilot.pause()

            comment_block = app.query_one(CommentBlock)
            assert comment_block.editing is False

    @pytest.mark.asyncio
    async def test_on_key_ctrl_enter_in_comment_edit_mode(self):
        """Ctrl+Enter while editing comment should save comment edit."""
        from textual.widgets import TextArea

        messages = []
        comment = Comment(
            id="c_ctrl",
            body="My comment",
            author=make_user(username="me"),
            created_at=datetime.now(),
            likes=0,
            is_own=True,
        )
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

            def on_post_block_edit_comment_requested(self, event):
                messages.append(event)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            edit_btn = app.query_one("#comment-edit-c_ctrl", Button)
            edit_btn.press()
            await pilot.pause()
            await pilot.pause(delay=0.1)

            textarea = app.query_one("#edit-comment-body", TextArea)
            textarea.text = "Updated comment"
            await pilot.pause()

            await pilot.press("ctrl+enter")
            await pilot.pause()

            assert len(messages) == 1
            assert messages[0].new_body == "Updated comment"

    def test_is_ancestor_of_returns_false(self):
        """is_ancestor_of should return False for unrelated widgets."""
        post = make_post()
        widget1 = PostBlock(post)
        widget2 = PostBlock(post)
        assert widget1.is_ancestor_of(widget2) is False


class TestPostBlockFocusEditButtonException:
    """Tests for _focus_edit_button exception path (lines 729-730)."""

    @pytest.mark.asyncio
    async def test_focus_edit_button_no_button(self):
        """_focus_edit_button should not crash when button doesn't exist."""
        post = make_post(is_own=False)  # No edit button

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)
            # Should not crash
            post_block._focus_edit_button()
            await pilot.pause()


class TestPostBlockFocusCommentEditTextarea:
    """Tests for _focus_comment_edit_textarea NoMatches (lines 766-767)."""

    @pytest.mark.asyncio
    async def test_focus_comment_edit_textarea_no_textarea(self):
        """_focus_comment_edit_textarea should handle NoMatches."""
        post = make_post()

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)
            # No editing textarea exists - should not crash
            post_block._focus_comment_edit_textarea()
            await pilot.pause()


class TestPostBlockFocusCommentEditButton:
    """Tests for _focus_comment_edit_button NoMatches (lines 790-791)."""

    @pytest.mark.asyncio
    async def test_focus_comment_edit_button_no_button(self):
        """_focus_comment_edit_button should handle NoMatches."""
        post = make_post()

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)
            # No such button - should not crash
            post_block._focus_comment_edit_button("nonexistent")
            await pilot.pause()


class TestPostBlockCommentDeleteConfirmation:
    """Tests for _cancel_comment_delete_confirmation (lines 815-819)."""

    @pytest.mark.asyncio
    async def test_cancel_comment_delete_resets_flag(self):
        """_cancel_comment_delete_confirmation should reset confirming_delete."""
        comment = Comment(
            id="c_cdel2",
            body="Comment to delete",
            author=make_user(username="me"),
            created_at=datetime.now(),
            likes=0,
            is_own=True,
        )
        post = make_post(comments=[comment])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            post_block.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Click Delete on comment
            delete_btn = app.query_one("#comment-delete-c_cdel2", Button)
            delete_btn.press()
            await pilot.pause()

            # Confirm delete is showing
            comment_block = app.query_one(CommentBlock)
            assert comment_block.confirming_delete is True

            # Cancel it
            cancel_btn = app.query_one("#comment-cancel-delete-c_cdel2", Button)
            cancel_btn.press()
            await pilot.pause()

            comment_block = app.query_one(CommentBlock)
            assert comment_block.confirming_delete is False


class TestPostBlockOnKeyPostMode:
    """Tests for on_key in post mode with focus edge cases."""

    @pytest.mark.asyncio
    async def test_on_key_focused_is_self_returns(self):
        """on_key should return when focused widget is self."""
        post = make_post()

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            post_block = app.query_one(PostBlock)

            # Enter post mode, then manually focus the block itself
            post_block.post_mode = True
            post_block.focus()
            await pilot.pause()

            # Press key - should not crash (returns early because focused is self)
            await pilot.press("tab")
            await pilot.pause()

    @pytest.mark.asyncio
    async def test_on_key_focus_outside_post_returns(self):
        """on_key should return when focused widget is outside post."""
        from textual.containers import Vertical

        post1 = make_post(id="p1")
        post2 = make_post(id="p2")

        class TestApp(App):
            def compose(self):
                with Vertical():
                    yield PostBlock(post1)
                    yield PostBlock(post2)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            blocks = list(app.query(PostBlock))
            first = blocks[0]
            second = blocks[1]

            # Enter post mode on first
            first.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Focus second block (outside first)
            second.focus()
            await pilot.pause()

            # first.post_mode is True but focus is outside
            assert first.post_mode is True
            assert not first.is_ancestor_of(app.focused)


class TestPostBlockEditMessages:
    """Tests for edit/delete post message classes."""

    def test_edit_post_requested_message(self):
        """EditPostRequested should store post and new_body."""
        post = make_post()
        msg = PostBlock.EditPostRequested(post, "new body")
        assert msg.post is post
        assert msg.new_body == "new body"

    def test_delete_post_requested_message(self):
        """DeletePostRequested should store post."""
        post = make_post()
        msg = PostBlock.DeletePostRequested(post)
        assert msg.post is post

    def test_edit_comment_requested_message(self):
        """EditCommentRequested should store comment and new_body."""
        comment = make_comment()
        msg = PostBlock.EditCommentRequested(comment, "new body")
        assert msg.comment is comment
        assert msg.new_body == "new body"

    def test_delete_comment_requested_message(self):
        """DeleteCommentRequested should store comment."""
        comment = make_comment()
        msg = PostBlock.DeleteCommentRequested(comment)
        assert msg.comment is comment

    def test_attachment_opened_message(self):
        """AttachmentOpened should store attachment."""
        att = Attachment(
            id="att1",
            file_name="file.txt",
            file_size=100,
            media_type="text/plain",
            url="https://example.com/file",
        )
        msg = PostBlock.AttachmentOpened(att)
        assert msg.attachment is att
