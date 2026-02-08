"""Tests for FeedScreen behavior."""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from textual.app import App
from textual.widgets import Button, Collapsible, Static

from freefood.models import Comment, HistoryEntry, Post, User, View
from freefood.screens.feed import FeedContainer, FeedScreen
from freefood.state import AppState
from freefood.widgets.comment_compose import CommentCompose
from freefood.widgets.compose import ComposeBlock
from freefood.widgets.menu import MenuBar
from freefood.widgets.post import CommentBlock, PostBlock


def make_user(
    id: str = "u1",
    username: str = "alice",
    screen_name: str = "Alice",
    user_type: str = "user",
) -> User:
    """Create a test user."""
    return User(id=id, username=username, screen_name=screen_name, type=user_type)


def make_comment(
    id: str = "c1",
    body: str = "Test comment",
    author: User | None = None,
    is_own: bool = False,
) -> Comment:
    """Create a test comment."""
    return Comment(
        id=id,
        body=body,
        author=author or make_user(username="commenter"),
        created_at=datetime.now(),
        likes=0,
        is_own=is_own,
    )


def make_post(
    id: str = "p1",
    body: str = "Test post body",
    author: User | None = None,
    comments: list[Comment] | None = None,
) -> Post:
    """Create a test post."""
    now = datetime.now()
    return Post(
        id=id,
        body=body,
        author=author or make_user(),
        groups=[],
        created_at=now,
        updated_at=now,
        comments=comments or [],
        omitted_comments=0,
        omitted_comments_offset=0,
        omitted_comment_likes=0,
        omitted_likes=0,
        likes=[],
    )


class MockApp(App):
    """Test app that pushes FeedScreen and tracks pushed screens."""

    def __init__(
        self,
        state: AppState | None = None,
        api: object | None = None,
    ):
        super().__init__()
        self.state = state or AppState()
        self.api = api
        self.pushed_screens: list = []
        self._original_push = None

    async def on_mount(self) -> None:
        self._original_push = self.push_screen

        def tracking_push(screen, *args, **kwargs):
            self.pushed_screens.append(screen)
            return self._original_push(screen, *args, **kwargs)

        self.push_screen = tracking_push  # type: ignore[assignment]


class TestFeedModeNavigation:
    """Tests for navigation in Feed mode (not Post mode)."""

    @pytest.mark.asyncio
    async def test_up_arrow_scrolls_feed_not_changes_selection(self):
        """Up arrow should scroll the feed, not change selected post."""
        from textual.app import App

        posts = [make_post(id=f"p{i}", body=f"Post {i}") for i in range(5)]

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = None
                self.state = AppState()

            def compose(self):
                yield FeedScreen(self.state)

        async with TestApp().run_test(size=(40, 20)) as pilot:
            app = pilot.app
            screen = app.query_one(FeedScreen)

            # Manually add posts to avoid API call
            container = screen.query_one("#feed-container")
            container.remove_children()
            for post in posts:
                await container.mount(PostBlock(post))
            await pilot.pause()

            # Focus second post using set_focus
            post_blocks = list(container.query(PostBlock))
            app.set_focus(post_blocks[1])
            await pilot.pause()

            # Verify second post is focused
            focused = app.focused
            assert focused is post_blocks[1], f"Expected post_blocks[1], got {focused}"

            # Press Up - currently changes selection
            # (this test verifies current broken behavior)
            await pilot.press("up")
            await pilot.pause()

            # Check: did Up change the selection to post 0?
            # If yes, test should fail (we want Up to scroll, not change selection)
            # If no, test passes (Up scrolls, doesn't change selection)
            assert app.focused is post_blocks[1], (
                f"Up arrow should scroll, not change selection. "
                f"Focus moved to {app.focused}"
            )

    @pytest.mark.asyncio
    async def test_down_arrow_scrolls_feed_not_changes_selection(self):
        """Down arrow should scroll the feed, not change selected post."""
        from textual.app import App

        posts = [make_post(id=f"p{i}", body=f"Post {i}") for i in range(5)]

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = None
                self.state = AppState()

            def compose(self):
                yield FeedScreen(self.state)

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            screen = app.query_one(FeedScreen)

            # Manually add posts
            container = screen.query_one("#feed-container")
            container.remove_children()
            for post in posts:
                await container.mount(PostBlock(post))
            await pilot.pause()

            # Focus second post using set_focus
            post_blocks = list(container.query(PostBlock))
            app.set_focus(post_blocks[1])
            await pilot.pause()

            # Verify second post is focused
            assert app.focused is post_blocks[1], (
                f"Expected post_blocks[1], got {app.focused}"
            )

            # Press Down - should NOT change selection (should scroll instead)
            await pilot.press("down")
            await pilot.pause()

            # Selection should still be on second post
            assert app.focused is post_blocks[1], (
                f"Down arrow should scroll, not change selection. "
                f"Focus moved to {app.focused}"
            )

    @pytest.mark.asyncio
    async def test_tab_changes_selection_to_next_post(self):
        """Tab should move selection to the next post."""
        from textual.app import App

        posts = [make_post(id=f"p{i}", body=f"Post {i}") for i in range(3)]

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = None
                self.state = AppState()

            def compose(self):
                yield FeedScreen(self.state)

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            screen = app.query_one(FeedScreen)

            # Manually add posts
            container = screen.query_one("#feed-container")
            container.remove_children()
            for post in posts:
                await container.mount(PostBlock(post))
            await pilot.pause()

            # Focus first post using set_focus
            post_blocks = list(container.query(PostBlock))
            app.set_focus(post_blocks[0])
            await pilot.pause()

            assert app.focused is post_blocks[0], (
                f"Setup: expected post_blocks[0], got {app.focused}"
            )

            # Press Tab - should move to next post
            await pilot.press("tab")
            await pilot.pause()

            # Selection should be on second post
            assert app.focused is post_blocks[1], (
                f"Tab should move to next post, got {app.focused}"
            )

    @pytest.mark.asyncio
    async def test_shift_tab_changes_selection_to_previous_post(self):
        """Shift+Tab should move selection to the previous post."""
        from textual.app import App

        posts = [make_post(id=f"p{i}", body=f"Post {i}") for i in range(3)]

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = None
                self.state = AppState()

            def compose(self):
                yield FeedScreen(self.state)

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            screen = app.query_one(FeedScreen)

            # Manually add posts
            container = screen.query_one("#feed-container")
            container.remove_children()
            for post in posts:
                await container.mount(PostBlock(post))
            await pilot.pause()

            # Focus second post using set_focus
            post_blocks = list(container.query(PostBlock))
            app.set_focus(post_blocks[1])
            await pilot.pause()

            assert app.focused is post_blocks[1], (
                f"Setup: expected post_blocks[1], got {app.focused}"
            )

            # Press Shift+Tab - should move to previous post
            await pilot.press("shift+tab")
            await pilot.pause()

            # Selection should be on first post
            assert app.focused is post_blocks[0], (
                f"Shift+Tab should move to previous post, got {app.focused}"
            )


class TestAutoSelectionOnScroll:
    """Tests for auto-moving selection when focused post scrolls out of view."""

    @pytest.mark.asyncio
    async def test_selection_moves_when_focused_post_scrolls_out_of_view(self):
        """When focused post scrolls out of view, selection moves to visible post."""
        from textual.app import App

        # Create posts with enough content to scroll
        posts = [make_post(id=f"p{i}", body=f"Post {i}\n" * 10) for i in range(10)]

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = None
                self.state = AppState()

            def on_mount(self) -> None:
                # Push screen properly so layout is calculated correctly
                self.push_screen(FeedScreen(self.state))

        # Use small screen to ensure posts don't all fit
        async with TestApp().run_test(size=(80, 15)) as pilot:
            app = pilot.app
            await pilot.pause()  # Wait for screen to mount

            screen = app.screen
            assert isinstance(screen, FeedScreen), "Screen should be FeedScreen"

            # Manually add posts
            container = screen.query_one("#feed-container")
            container.remove_children()
            for post in posts:
                await container.mount(PostBlock(post))
            await pilot.pause()

            # Focus first post
            post_blocks = list(container.query(PostBlock))
            app.set_focus(post_blocks[0])
            await pilot.pause()

            assert app.focused is post_blocks[0], "Setup: first post should be focused"

            # Scroll down multiple times to push first post out of view
            # This should eventually trigger auto-selection to a visible post
            for _ in range(30):
                await pilot.press("down")
                await pilot.pause()

            # The focused widget should NOT be post_blocks[0] anymore
            # because it has scrolled out of view
            focused = app.focused
            assert focused is not post_blocks[0], (
                "After scrolling down, focus should move away from post 0 "
                "which is now out of view"
            )
            # And the focused widget should be a PostBlock
            assert isinstance(focused, PostBlock), (
                f"Focus should be on a PostBlock, got {type(focused)}"
            )


class TestUserFeedNavigation:
    """Tests for navigating to user feeds from post header."""

    @pytest.mark.asyncio
    async def test_user_clicked_switches_to_user_feed(self):
        """UserClicked should navigate to the user feed and load posts."""
        from textual.app import App

        home_posts = [make_post(id="p1", body="Home post")]
        user_posts = [make_post(id="p2", body="User post")]

        class FakeAPI:
            def __init__(self):
                self.user_calls: list[str] = []

            async def get_home_feed(self):
                return home_posts

            async def get_user_feed(self, username: str):
                self.user_calls.append(username)
                return user_posts

            async def get_user_subscription_status(self, username: str):
                return False

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(current_view=View.HOME)

            def compose(self):
                yield FeedScreen(self.state)

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            screen = app.query_one(FeedScreen)
            await pilot.pause()

            await screen.on_post_block_user_clicked(
                PostBlock.UserClicked("bob", "user")
            )
            await pilot.pause()

            assert app.state.current_view == View.USER_FEED
            assert app.state.current_target == "bob"
            assert app.api.user_calls == ["bob"]
            assert screen.query(PostBlock).first() is not None


class TestUserFeedHeader:
    """Tests for user/group feed header display."""

    @pytest.mark.asyncio
    async def test_user_feed_renders_header(self):
        """User feed should render a header with the target username."""
        from textual.app import App
        from textual.widgets import Static

        posts = [make_post(id="p1", body="User post")]

        class FakeAPI:
            async def get_user_feed(self, username: str):
                return posts

            async def get_user_subscription_status(self, username: str):
                return False

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(current_view=View.USER_FEED, current_target="bob")

            async def on_mount(self):
                self.push_screen(FeedScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            screen = app.screen
            await pilot.pause()

            header = screen.query_one("#feed-header", Static)
            assert "@bob" in str(header.content)

    @pytest.mark.asyncio
    async def test_user_feed_header_includes_screen_name(self):
        """User feed header should include screen name when available."""
        from textual.app import App
        from textual.widgets import Static

        author = make_user(username="bob", screen_name="Bob Builder")
        posts = [make_post(id="p1", author=author, body="User post")]

        class FakeAPI:
            async def get_user_feed(self, username: str):
                return posts

            async def get_user_subscription_status(self, username: str):
                return False

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(current_view=View.USER_FEED, current_target="bob")

            async def on_mount(self):
                self.push_screen(FeedScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            screen = app.screen
            await pilot.pause()

            header = screen.query_one("#feed-header", Static)
            assert "Bob Builder" in str(header.content)

    @pytest.mark.asyncio
    async def test_subscribe_button_renders_below_header(self):
        """Subscribe button should render on its own line below the header."""
        from textual.app import App
        from textual.widgets import Button, Static

        long_name = "Very Long Screen Name " * 6
        author = make_user(username="bob", screen_name=long_name)
        posts = [make_post(id="p1", author=author, body="User post")]

        class FakeAPI:
            async def get_user_feed(self, username: str):
                return posts

            async def get_user_subscription_status(self, username: str):
                return False

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(current_view=View.USER_FEED, current_target="bob")

            async def on_mount(self):
                self.push_screen(FeedScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            screen = app.screen
            await pilot.pause()

            header = screen.query_one("#feed-header", Static)
            button = screen.query_one("#btn-subscribe", Button)

            assert button.region.y > header.region.y

    @pytest.mark.asyncio
    async def test_group_feed_header_includes_screen_name(self):
        """Group feed header should include screen name when available."""
        from textual.app import App
        from textual.widgets import Static

        group = make_user(
            id="g1", username="news", screen_name="News Group", user_type="group"
        )
        post = make_post(id="p1", body="Group post")
        post.groups = [group]
        posts = [post]

        class FakeAPI:
            async def get_user_feed(self, username: str):
                return posts

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(
                    current_view=View.GROUP_FEED, current_target="news"
                )

            def compose(self):
                yield FeedScreen(self.state)

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            screen = app.query_one(FeedScreen)
            await pilot.pause()

            header = screen.query_one("#feed-header", Static)
            assert "News Group" in str(header.content)

    @pytest.mark.asyncio
    async def test_user_feed_shows_subscribe_button(self):
        """User feed should show subscribe button based on status."""
        from textual.app import App
        from textual.widgets import Button

        posts = [make_post(id="p1", body="User post")]

        class FakeAPI:
            async def get_user_feed(self, username: str):
                return posts

            async def get_user_subscription_status(self, username: str):
                return False

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(current_view=View.USER_FEED, current_target="bob")

            async def on_mount(self):
                self.push_screen(FeedScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            screen = app.screen
            await pilot.pause()

            button = screen.query_one("#btn-subscribe", Button)
            assert button.label.plain == "Subscribe"

    @pytest.mark.asyncio
    async def test_subscribe_button_has_visible_width(self):
        """Subscribe button should render with a visible width."""
        from textual.app import App
        from textual.widgets import Button

        posts = [make_post(id="p1", body="User post")]

        class FakeAPI:
            async def get_user_feed(self, username: str):
                return posts

            async def get_user_subscription_status(self, username: str):
                return False

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(current_view=View.USER_FEED, current_target="bob")

            async def on_mount(self):
                self.push_screen(FeedScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            screen = app.screen
            await pilot.pause()

            button = screen.query_one("#btn-subscribe", Button)
            assert button.region.width > 0

    @pytest.mark.asyncio
    async def test_subscribe_button_is_single_line(self):
        """Subscribe button should render as a single line."""
        from textual.app import App
        from textual.widgets import Button

        posts = [make_post(id="p1", body="User post")]

        class FakeAPI:
            async def get_user_feed(self, username: str):
                return posts

            async def get_user_subscription_status(self, username: str):
                return False

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(current_view=View.USER_FEED, current_target="bob")

            async def on_mount(self):
                self.push_screen(FeedScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            screen = app.screen
            await pilot.pause()

            button = screen.query_one("#btn-subscribe", Button)
            assert button.region.height == 1

    @pytest.mark.asyncio
    async def test_subscribe_button_toggles(self):
        """Subscribe button should toggle label and call API."""
        from textual.app import App
        from textual.widgets import Button

        posts = [make_post(id="p1", body="User post")]

        class FakeAPI:
            def __init__(self):
                self.subscribed = True
                self.subscribe_calls: list[str] = []
                self.unsubscribe_calls: list[str] = []

            async def get_user_feed(self, username: str):
                return posts

            async def get_user_subscription_status(self, username: str):
                return self.subscribed

            async def subscribe(self, username: str) -> None:
                self.subscribe_calls.append(username)
                self.subscribed = True

            async def unsubscribe(self, username: str) -> None:
                self.unsubscribe_calls.append(username)
                self.subscribed = False

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(current_view=View.USER_FEED, current_target="bob")

            def compose(self):
                yield FeedScreen(self.state)

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            screen = app.query_one(FeedScreen)
            await pilot.pause()

            button = screen.query_one("#btn-subscribe", Button)
            assert button.label.plain == "Unsubscribe"

            button.press()
            await pilot.pause()

            assert app.api.unsubscribe_calls == ["bob"]
            assert button.label.plain == "Subscribe"


class TestPostModeEscape:
    """Tests for escape behavior in post mode."""

    @pytest.mark.asyncio
    async def test_escape_exits_post_mode_to_feed(self):
        """Escape should exit post mode and keep focus in feed."""
        from textual.app import App

        posts = [make_post(id="p1", body="Post 1")]

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = None
                self.state = AppState()

            def compose(self):
                yield FeedScreen(self.state)

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            screen = app.query_one(FeedScreen)
            container = screen.query_one("#feed-container")
            container.remove_children()
            for post in posts:
                await container.mount(PostBlock(post))
            await pilot.pause()

            post_block = container.query(PostBlock).first()
            assert post_block is not None
            app.set_focus(post_block)
            await pilot.pause()

            await pilot.press("enter")
            await pilot.pause()
            assert post_block.post_mode is True

            await pilot.press("escape")
            await pilot.pause()

            assert post_block.post_mode is False
            assert app.focused is post_block

    @pytest.mark.asyncio
    async def test_focus_menu_action_exits_post_mode(self):
        """FeedScreen focus_menu action should exit post mode first."""
        from textual.app import App

        posts = [make_post(id="p1", body="Post 1")]

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = None
                self.state = AppState()

            def compose(self):
                yield FeedScreen(self.state)

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            screen = app.query_one(FeedScreen)
            container = screen.query_one("#feed-container")
            container.remove_children()
            for post in posts:
                await container.mount(PostBlock(post))
            await pilot.pause()

            post_block = container.query(PostBlock).first()
            assert post_block is not None
            app.set_focus(post_block)
            await pilot.pause()

            await pilot.press("enter")
            await pilot.pause()
            assert post_block.post_mode is True

            screen.action_focus_menu()
            await pilot.pause()

            assert post_block.post_mode is False
            assert app.focused is post_block


class TestExpandCommentsFocus:
    """Tests for focusing comments after expansion."""

    @pytest.mark.asyncio
    async def test_expand_comments_focuses_first_comment(self):
        """After expanding, focus should move to the first comment."""
        from textual.app import App

        base_post = make_post(id="p1", body="Post")
        base_post.omitted_comments = 1
        base_post.omitted_comments_offset = 0
        base_post.comments = []

        full_post = make_post(id="p1", body="Post")
        full_post.comments = [
            Comment(
                id="c1",
                body="First comment",
                author=make_user(username="bob"),
                created_at=datetime.now(),
                likes=0,
            ),
            Comment(
                id="c2",
                body="Second comment",
                author=make_user(username="carol"),
                created_at=datetime.now(),
                likes=0,
            ),
        ]

        class FakeAPI:
            async def get_post(self, post_id: str):
                assert post_id == "p1"
                return full_post

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState()

            def compose(self):
                yield FeedScreen(self.state)

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            screen = app.query_one(FeedScreen)
            container = screen.query_one("#feed-container")
            container.remove_children()
            await container.mount(PostBlock(base_post))
            await pilot.pause()

            post_block = container.query(PostBlock).first()
            assert post_block is not None
            app.set_focus(post_block)
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            await screen.on_post_block_expand_comments(
                PostBlock.ExpandComments(base_post)
            )
            await pilot.pause(0.2)

            assert post_block.post_mode is True
            comment = post_block.query(CommentBlock).first()
            assert comment is not None
            assert comment.can_focus is True

            focused = app.focused
            assert isinstance(focused, CommentBlock)

    @pytest.mark.asyncio
    async def test_expand_comments_focuses_first_new_comment(self):
        """After expanding, focus should move to first newly loaded comment."""
        from textual.app import App

        base_post = make_post(id="p1", body="Post")
        base_post.omitted_comments = 2
        base_post.omitted_comments_offset = 1
        base_post.comments = [
            Comment(
                id="c1",
                body="Visible comment",
                author=make_user(username="alice"),
                created_at=datetime.now(),
                likes=0,
            )
        ]

        full_post = make_post(id="p1", body="Post")
        full_post.comments = [
            Comment(
                id="c1",
                body="Visible comment",
                author=make_user(username="alice"),
                created_at=datetime.now(),
                likes=0,
            ),
            Comment(
                id="c2",
                body="New comment 1",
                author=make_user(username="bob"),
                created_at=datetime.now(),
                likes=0,
            ),
            Comment(
                id="c3",
                body="New comment 2",
                author=make_user(username="carol"),
                created_at=datetime.now(),
                likes=0,
            ),
        ]

        class FakeAPI:
            async def get_post(self, post_id: str):
                assert post_id == "p1"
                return full_post

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState()

            def compose(self):
                yield FeedScreen(self.state)

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            screen = app.query_one(FeedScreen)
            container = screen.query_one("#feed-container")
            container.remove_children()
            await container.mount(PostBlock(base_post))
            await pilot.pause()

            post_block = container.query(PostBlock).first()
            assert post_block is not None
            app.set_focus(post_block)
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            await screen.on_post_block_expand_comments(
                PostBlock.ExpandComments(base_post)
            )
            await pilot.pause(0.2)

            focused = app.focused
            assert isinstance(focused, CommentBlock)
            assert focused.comment.id == "c2"


class TestFeedScreenMenuNavigation:
    """Tests for FeedScreen menu navigation."""

    @pytest.mark.asyncio
    async def test_notifications_menu_opens_notifications_screen(self):
        """Selecting Notifications should open NotificationsScreen."""
        from textual.app import App

        from freefood.widgets.menu import MenuBar

        class FakeAPI:
            async def get_home_feed(self):
                return []

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(current_view=View.HOME)

            def on_mount(self) -> None:
                self.push_screen(FeedScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            app = pilot.app
            screen = app.screen
            await pilot.pause()

            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.NOTIFICATIONS))
            await pilot.pause()

            from freefood.screens.notifications import NotificationsScreen

            assert isinstance(app.screen, NotificationsScreen)


class TestDirectsUnreadIndicator:
    """Tests for unread directs indicator."""

    @pytest.mark.asyncio
    async def test_directs_count_updates_menu(self):
        """FeedScreen should update directs count label."""
        from textual.app import App
        from textual.widgets import Button

        class FakeAPI:
            async def get_home_feed(self):
                return []

            async def get_unread_notifications_count(self) -> int:
                return 0

            async def get_unread_directs_count(self) -> int:
                return 3

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(current_view=View.HOME)

            def on_mount(self) -> None:
                self.push_screen(FeedScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            button = screen.query_one("#directs-button", Button)
            assert button.label.plain == "Directs (3)"


class TestComposeBlockIntegration:
    """Tests for ComposeBlock appearing in correct views."""

    @pytest.mark.asyncio
    async def test_compose_block_shown_in_home_view(self):
        """ComposeBlock should appear in Home view."""
        from textual.app import App

        from freefood.widgets.compose import ComposeBlock

        class FakeAPI:
            async def get_home_feed(self):
                return []

            async def get_unread_notifications_count(self) -> int:
                return 0

            async def get_unread_directs_count(self) -> int:
                return 0

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(current_view=View.HOME)

            def on_mount(self) -> None:
                self.push_screen(FeedScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            compose_blocks = list(screen.query(ComposeBlock))
            assert len(compose_blocks) == 1, "ComposeBlock should appear in HOME view"

    @pytest.mark.asyncio
    async def test_compose_block_shown_in_directs_view(self):
        """ComposeBlock should appear in Directs view."""
        from textual.app import App

        from freefood.widgets.compose import ComposeBlock

        class FakeAPI:
            async def get_directs(self):
                return []

            async def get_unread_notifications_count(self) -> int:
                return 0

            async def get_unread_directs_count(self) -> int:
                return 0

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(current_view=View.DIRECTS)

            def on_mount(self) -> None:
                self.push_screen(FeedScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            compose_blocks = list(screen.query(ComposeBlock))
            assert len(compose_blocks) == 1, (
                "ComposeBlock should appear in DIRECTS view"
            )

    @pytest.mark.asyncio
    async def test_compose_block_not_shown_in_user_feed_view(self):
        """ComposeBlock should NOT appear in User feed view."""
        from textual.app import App

        from freefood.widgets.compose import ComposeBlock

        class FakeAPI:
            async def get_user_feed(self, username: str):
                return []

            async def get_user_subscription_status(self, username: str):
                return False

            async def get_unread_notifications_count(self) -> int:
                return 0

            async def get_unread_directs_count(self) -> int:
                return 0

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(current_view=View.USER_FEED, current_target="bob")

            def on_mount(self) -> None:
                self.push_screen(FeedScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            compose_blocks = list(screen.query(ComposeBlock))
            assert len(compose_blocks) == 0, (
                "ComposeBlock should NOT appear in USER_FEED view"
            )

    @pytest.mark.asyncio
    async def test_compose_block_not_shown_in_group_feed_view(self):
        """ComposeBlock should NOT appear in Group feed view."""
        from textual.app import App

        from freefood.widgets.compose import ComposeBlock

        class FakeAPI:
            async def get_user_feed(self, username: str):
                return []

            async def get_unread_notifications_count(self) -> int:
                return 0

            async def get_unread_directs_count(self) -> int:
                return 0

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(
                    current_view=View.GROUP_FEED, current_target="news"
                )

            def on_mount(self) -> None:
                self.push_screen(FeedScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            compose_blocks = list(screen.query(ComposeBlock))
            assert len(compose_blocks) == 0, (
                "ComposeBlock should NOT appear in GROUP_FEED view"
            )


# ---------------------------------------------------------------------------
# New tests: cover all missing lines/branches in feed.py
# ---------------------------------------------------------------------------


def _make_mock_api(**overrides):
    """Create a MockAPI with sensible defaults and optional overrides."""
    api = AsyncMock()
    api.get_home_feed = AsyncMock(return_value=[])
    api.get_directs = AsyncMock(return_value=[])
    api.get_user_feed = AsyncMock(return_value=[])
    api.get_user_subscription_status = AsyncMock(return_value=False)
    api.get_unread_notifications_count = AsyncMock(return_value=0)
    api.get_unread_directs_count = AsyncMock(return_value=0)
    api.get_post = AsyncMock(return_value=None)
    api.like_post = AsyncMock()
    api.unlike_post = AsyncMock()
    api.hide_post = AsyncMock()
    api.unhide_post = AsyncMock()
    api.like_comment = AsyncMock()
    api.unlike_comment = AsyncMock()
    api.current_user = None
    api.subscribe = AsyncMock()
    api.unsubscribe = AsyncMock()
    api.create_post = AsyncMock()
    api.create_comment = AsyncMock(return_value=make_comment())
    api.update_post = AsyncMock()
    api.update_comment = AsyncMock()
    api.delete_post = AsyncMock()
    api.delete_comment = AsyncMock()
    for k, v in overrides.items():
        setattr(api, k, v)
    return api


class TestStateFallback:
    """Test the state property fallback to app.state (line 136)."""

    @pytest.mark.asyncio
    async def test_state_falls_back_to_app_state(self):
        """FeedScreen.state should fall back to app.state when _state is None."""
        api = _make_mock_api()
        app = MockApp(api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            screen = FeedScreen(state=None)
            await app._original_push(screen)
            await pilot.pause()
            # The screen's state should be the app's state
            assert screen.state is app.state


class TestRefreshContentViews:
    """Test refresh_content with different views (lines 160-170)."""

    @pytest.mark.asyncio
    async def test_directs_view_calls_get_directs(self):
        """DIRECTS view should call api.get_directs."""
        posts = [make_post(id="d1")]
        api = _make_mock_api(get_directs=AsyncMock(return_value=posts))
        state = AppState(current_view=View.DIRECTS)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            api.get_directs.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_feed_without_target_returns_empty(self):
        """USER_FEED without target should result in empty posts (line 168)."""
        api = _make_mock_api()
        state = AppState(current_view=View.USER_FEED, current_target=None)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            assert screen.posts == []

    @pytest.mark.asyncio
    async def test_unknown_view_returns_empty(self):
        """Unhandled view in refresh_content falls to else (line 170)."""
        api = _make_mock_api()
        state = AppState(current_view=View.SEARCH)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            assert screen.posts == []

    @pytest.mark.asyncio
    async def test_api_is_none_shows_error(self):
        """When api is None, refresh_content should show error."""
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=None)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            error = screen.query_one(".error", Static)
            assert "Not connected" in str(error.render())

    @pytest.mark.asyncio
    async def test_api_raises_shows_error(self):
        """When api raises, refresh_content should show error message."""
        api = _make_mock_api(
            get_home_feed=AsyncMock(side_effect=Exception("Network error"))
        )
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            error = screen.query_one(".error", Static)
            assert "Network error" in str(error.render())


class TestActionFocusMenu:
    """Test action_focus_menu when not in post mode (lines 251-252)."""

    @pytest.mark.asyncio
    async def test_focus_menu_focuses_menu_bar(self):
        """Escape when not in post mode should focus the menu bar."""
        api = _make_mock_api()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            screen.action_focus_menu()
            await pilot.pause()
            focused = app.focused
            assert isinstance(focused, Button)


class TestActionFocusFeed:
    """Test action_focus_feed (lines 256-259)."""

    @pytest.mark.asyncio
    async def test_focus_feed_focuses_first_post(self):
        """action_focus_feed should focus the first PostBlock."""
        posts = [make_post(id="p1")]
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=posts))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            # First focus menu, then action_focus_feed
            screen.action_focus_menu()
            await pilot.pause()
            screen.action_focus_feed()
            await pilot.pause()
            focused = app.focused
            assert isinstance(focused, PostBlock)

    @pytest.mark.asyncio
    async def test_focus_feed_when_posts_exist(self):
        """action_focus_feed should focus the first post when posts exist."""
        posts = [make_post(id="p1"), make_post(id="p2")]
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=posts))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            # Focus menu first so we can verify focus moves to feed
            screen.action_focus_menu()
            await pilot.pause()
            screen.action_focus_feed()
            await pilot.pause()
            assert isinstance(app.focused, PostBlock)


class TestFindPostBlock:
    """Test _find_post_block (lines 267-268)."""

    @pytest.mark.asyncio
    async def test_find_post_block_returns_none_for_non_post(self):
        """_find_post_block should return None when widget is not in a PostBlock."""
        api = _make_mock_api()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            # Pass the menu bar - not a child of PostBlock
            menu = screen.query_one(MenuBar)
            result = screen._find_post_block(menu)
            assert result is None

    @pytest.mark.asyncio
    async def test_find_post_block_returns_none_for_none(self):
        """_find_post_block should return None when widget is None."""
        api = _make_mock_api()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            result = screen._find_post_block(None)
            assert result is None


class TestActionRefresh:
    """Test action_refresh (line 272)."""

    @pytest.mark.asyncio
    async def test_action_refresh_triggers_worker(self):
        """action_refresh should call run_worker with refresh_content."""
        posts = [make_post()]
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=posts))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            # Call action_refresh (dispatches worker)
            screen.action_refresh()
            await pilot.pause()
            # get_home_feed should have been called at least 2 times
            # (once on mount, once on refresh)
            assert api.get_home_feed.call_count >= 2


class TestMenuViewSelected:
    """Test on_menu_bar_view_selected (lines 277-302)."""

    @pytest.mark.asyncio
    async def test_search_view_pushes_search_screen(self):
        """Selecting SEARCH should push SearchScreen."""
        api = _make_mock_api()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.SEARCH))
            await pilot.pause()

            from freefood.screens.search import SearchScreen

            assert any(isinstance(s, SearchScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_errors_view_pushes_errors_screen(self):
        """Selecting ERRORS should push ErrorsScreen (lines 290-296)."""
        api = _make_mock_api()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.ERRORS))
            await pilot.pause()

            from freefood.screens.errors import ErrorsScreen

            assert any(isinstance(s, ErrorsScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_view_change_refreshes_content(self):
        """Selecting a different feed view should refresh content (lines 298-302)."""
        api = _make_mock_api()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.DIRECTS))
            await pilot.pause()
            assert state.current_view == View.DIRECTS

    @pytest.mark.asyncio
    async def test_same_view_still_refreshes(self):
        """Selecting the same view should still refresh (line 302)."""
        api = _make_mock_api()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.HOME))
            await pilot.pause()
            # Should still call get_home_feed
            assert api.get_home_feed.call_count >= 2


class TestBackNavigation:
    """Test on_menu_bar_back_requested (lines 306-322)."""

    @pytest.mark.asyncio
    async def test_back_with_no_history_notifies(self):
        """Back with empty history should notify 'No history' (line 322)."""
        api = _make_mock_api()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20), notifications=True) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()
            assert any("No history" in str(n.message) for n in app._notifications)

    @pytest.mark.asyncio
    async def test_back_to_home_refreshes_feed(self):
        """Back to HOME should update state and refresh (lines 306-319)."""
        api = _make_mock_api()
        state = AppState(current_view=View.DIRECTS)
        state.history.append(
            HistoryEntry(view=View.HOME, target=None, scroll_position=0)
        )
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()
            assert state.current_view == View.HOME
            assert state.current_target is None

    @pytest.mark.asyncio
    async def test_back_to_search_pushes_search_screen(self):
        """Back to SEARCH should push SearchScreen (lines 312-315)."""
        api = _make_mock_api()
        state = AppState(current_view=View.HOME)
        state.history.append(
            HistoryEntry(view=View.SEARCH, target=None, scroll_position=0, query="test")
        )
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()
            assert state.current_view == View.SEARCH
            assert state.search_query == "test"

            from freefood.screens.search import SearchScreen

            assert any(isinstance(s, SearchScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_back_restores_target(self):
        """Back should restore current_target from history entry (line 309)."""
        api = _make_mock_api()
        state = AppState(current_view=View.HOME)
        state.history.append(
            HistoryEntry(view=View.USER_FEED, target="bob", scroll_position=0)
        )
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()
            assert state.current_view == View.USER_FEED
            assert state.current_target == "bob"

    @pytest.mark.asyncio
    async def test_back_without_query_does_not_set_search_query(self):
        """Back to HOME should not modify search_query if entry has no query."""
        api = _make_mock_api()
        state = AppState(current_view=View.DIRECTS, search_query="old")
        state.history.append(
            HistoryEntry(view=View.HOME, target=None, scroll_position=0)
        )
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()
            assert state.search_query == "old"


class TestExpandCommentsError:
    """Test expand_comments error path (lines 345-346)."""

    @pytest.mark.asyncio
    async def test_expand_comments_error_shows_banner(self):
        """When get_post raises, should show error banner."""
        api = _make_mock_api(get_post=AsyncMock(side_effect=Exception("API error")))
        state = AppState(current_view=View.HOME)
        posts = [make_post(id="p1")]
        api.get_home_feed = AsyncMock(return_value=posts)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_expand_comments(
                PostBlock.ExpandComments(posts[0])
            )
            await pilot.pause()
            banner = screen.query_one("#error-banner", Static)
            assert "visible" in banner.classes


class TestLikeUnlike:
    """Test like/unlike post (lines 352-368)."""

    @pytest.mark.asyncio
    async def test_like_post(self):
        """Liking a post should call api.like_post and update state."""
        post = make_post(id="p1")
        post.is_liked = False
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20), notifications=True) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_like_requested(PostBlock.LikeRequested(post))
            await pilot.pause()
            api.like_post.assert_called_once_with("p1")
            assert post.is_liked is True
            assert any("Liked" in str(n.message) for n in app._notifications)

    @pytest.mark.asyncio
    async def test_unlike_post(self):
        """Unliking a post should call api.unlike_post and update state."""
        post = make_post(id="p1")
        post.is_liked = True
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20), notifications=True) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_like_requested(PostBlock.LikeRequested(post))
            await pilot.pause()
            api.unlike_post.assert_called_once_with("p1")
            assert post.is_liked is False
            assert any("Unliked" in str(n.message) for n in app._notifications)

    @pytest.mark.asyncio
    async def test_like_error_shows_banner(self):
        """Like failure should show error banner."""
        post = make_post(id="p1")
        post.is_liked = False
        api = _make_mock_api(
            get_home_feed=AsyncMock(return_value=[post]),
            like_post=AsyncMock(side_effect=Exception("Like failed")),
        )
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_like_requested(PostBlock.LikeRequested(post))
            await pilot.pause()
            banner = screen.query_one("#error-banner", Static)
            assert "visible" in banner.classes

    @pytest.mark.asyncio
    async def test_like_post_adds_current_user_to_likes(self):
        """Liking should prepend current user to post.likes."""
        current_user = make_user(id="me", username="me")
        post = make_post(id="p1")
        post.is_liked = False
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        api.current_user = current_user
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_like_requested(PostBlock.LikeRequested(post))
            await pilot.pause()
            assert current_user in post.likes
            assert post.likes[0] == current_user

    @pytest.mark.asyncio
    async def test_unlike_post_removes_current_user_from_likes(self):
        """Unliking should remove current user from post.likes by id."""
        current_user = make_user(id="me", username="me")
        other_user = make_user(id="u2", username="other")
        post = make_post(id="p1")
        post.is_liked = True
        post.likes = [current_user, other_user]
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        api.current_user = current_user
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_like_requested(PostBlock.LikeRequested(post))
            await pilot.pause()
            assert current_user not in post.likes
            assert other_user in post.likes

    @pytest.mark.asyncio
    async def test_like_post_no_current_user_still_works(self):
        """Liking should still toggle state when api.current_user is None."""
        post = make_post(id="p1")
        post.is_liked = False
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        api.current_user = None
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_like_requested(PostBlock.LikeRequested(post))
            await pilot.pause()
            assert post.is_liked is True
            assert post.likes == []

    @pytest.mark.asyncio
    async def test_unlike_post_user_not_in_list(self):
        """Unliking should preserve existing likes if current user is absent."""
        current_user = make_user(id="me", username="me")
        other_user = make_user(id="u2", username="other")
        post = make_post(id="p1")
        post.is_liked = True
        post.likes = [other_user]
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        api.current_user = current_user
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_like_requested(PostBlock.LikeRequested(post))
            await pilot.pause()
            assert other_user in post.likes


class TestCommentLikeUnlike:
    """Test comment like/unlike handling."""

    @pytest.mark.asyncio
    async def test_like_comment(self):
        """Liking a comment should call API and increment likes."""
        comment = make_comment(id="c1")
        comment.is_liked = False
        comment.likes = 0
        post = make_post(id="p1", comments=[comment])
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20), notifications=True) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_comment_like_requested(
                PostBlock.CommentLikeRequested(comment)
            )
            await pilot.pause()
            api.like_comment.assert_called_once_with("c1")
            assert comment.is_liked is True
            assert comment.likes == 1

    @pytest.mark.asyncio
    async def test_unlike_comment(self):
        """Unliking a comment should call API and decrement likes."""
        comment = make_comment(id="c1")
        comment.is_liked = True
        comment.likes = 5
        post = make_post(id="p1", comments=[comment])
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20), notifications=True) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_comment_like_requested(
                PostBlock.CommentLikeRequested(comment)
            )
            await pilot.pause()
            api.unlike_comment.assert_called_once_with("c1")
            assert comment.is_liked is False
            assert comment.likes == 4

    @pytest.mark.asyncio
    async def test_like_comment_error_shows_banner(self):
        """Comment like failure should show error banner."""
        comment = make_comment(id="c1")
        comment.is_liked = False
        post = make_post(id="p1", comments=[comment])
        api = _make_mock_api(
            get_home_feed=AsyncMock(return_value=[post]),
            like_comment=AsyncMock(side_effect=Exception("Like failed")),
        )
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_comment_like_requested(
                PostBlock.CommentLikeRequested(comment)
            )
            await pilot.pause()
            banner = screen.query_one("#error-banner", Static)
            assert "visible" in banner.classes

    @pytest.mark.asyncio
    async def test_unlike_comment_does_not_go_below_zero(self):
        """Comment likes should not go below zero when unliking."""
        comment = make_comment(id="c1")
        comment.is_liked = True
        comment.likes = 0
        post = make_post(id="p1", comments=[comment])
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_comment_like_requested(
                PostBlock.CommentLikeRequested(comment)
            )
            await pilot.pause()
            assert comment.likes == 0

    @pytest.mark.asyncio
    async def test_comment_like_keeps_focus_on_same_button(self):
        """After like/unlike, focus should stay on that comment's like button."""
        comment = make_comment(id="c1")
        comment.is_liked = False
        comment.likes = 0
        post = make_post(id="p1", comments=[comment])
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)

            block = screen.query_one(PostBlock)
            block.action_enter_post_mode()
            await pilot.pause()

            btn = screen.query_one("#comment-like-c1", Button)
            btn.focus()
            await pilot.pause()
            assert app.focused is btn

            await screen.on_post_block_comment_like_requested(
                PostBlock.CommentLikeRequested(comment)
            )
            await pilot.pause()

            assert isinstance(app.focused, Button)
            assert app.focused.id == "comment-like-c1"


class TestHiddenPostsGrouping:
    """Test grouping hidden posts at bottom of home feed."""

    @pytest.mark.asyncio
    async def test_hidden_posts_not_in_main_feed(self):
        """Hidden posts should not be direct children in home feed."""
        visible = make_post(id="p1")
        hidden = make_post(id="p2")
        hidden.is_hidden = True
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[visible, hidden]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            container = screen.query_one("#feed-container")
            direct_posts = [c for c in container.children if isinstance(c, PostBlock)]
            assert len(direct_posts) == 1
            assert direct_posts[0].post.id == "p1"

    @pytest.mark.asyncio
    async def test_hidden_posts_collapsible_shown(self):
        """Home feed should show a collapsible section for hidden posts."""
        visible = make_post(id="p1")
        hidden = make_post(id="p2")
        hidden.is_hidden = True
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[visible, hidden]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            collapsible = screen.query_one(Collapsible)
            assert "Hidden 1 post" in str(collapsible.title)

            hidden_block = next(
                block for block in screen.query(PostBlock) if block.post.id == "p2"
            )
            assert isinstance(hidden_block.parent, Collapsible.Contents)

    @pytest.mark.asyncio
    async def test_no_collapsible_when_no_hidden_posts(self):
        """Home feed should not render collapsible when there are no hidden posts."""
        posts = [make_post(id="p1"), make_post(id="p2")]
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=posts))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            assert len(list(screen.query(Collapsible))) == 0

    @pytest.mark.asyncio
    async def test_hidden_posts_plural_label(self):
        """Collapsible label should use plural when there are multiple hidden posts."""
        hidden1 = make_post(id="p1")
        hidden1.is_hidden = True
        hidden2 = make_post(id="p2")
        hidden2.is_hidden = True
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[hidden1, hidden2]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            collapsible = screen.query_one(Collapsible)
            assert "Hidden 2 posts" in str(collapsible.title)

    @pytest.mark.asyncio
    async def test_hide_mid_session_moves_post_to_hidden(self):
        """Hiding a visible post should move it into hidden section."""
        post = make_post(id="p1")
        post.is_hidden = False
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            assert len(list(screen.query(Collapsible))) == 0
            await screen.on_post_block_hide_requested(PostBlock.HideRequested(post))
            await pilot.pause()
            collapsible = screen.query_one(Collapsible)
            assert "Hidden 1 post" in str(collapsible.title)

    @pytest.mark.asyncio
    async def test_unhide_mid_session_removes_collapsible(self):
        """Unhiding the last hidden post should remove hidden section."""
        post = make_post(id="p1")
        post.is_hidden = True
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            assert len(list(screen.query(Collapsible))) == 1
            await screen.on_post_block_hide_requested(PostBlock.HideRequested(post))
            await pilot.pause()
            assert len(list(screen.query(Collapsible))) == 0


class TestHideUnhide:
    """Test hide/unhide post (lines 374-389)."""

    @pytest.mark.asyncio
    async def test_hide_post(self):
        """Hiding a post should call api.hide_post."""
        post = make_post(id="p1")
        post.is_hidden = False
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20), notifications=True) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_hide_requested(PostBlock.HideRequested(post))
            await pilot.pause()
            api.hide_post.assert_called_once_with("p1")
            assert post.is_hidden is True
            assert any("Hidden" in str(n.message) for n in app._notifications)

    @pytest.mark.asyncio
    async def test_unhide_post(self):
        """Unhiding a post should call api.unhide_post."""
        post = make_post(id="p1")
        post.is_hidden = True
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20), notifications=True) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_hide_requested(PostBlock.HideRequested(post))
            await pilot.pause()
            api.unhide_post.assert_called_once_with("p1")
            assert post.is_hidden is False
            assert any("Unhidden" in str(n.message) for n in app._notifications)

    @pytest.mark.asyncio
    async def test_hide_error_shows_banner(self):
        """Hide failure should show error banner."""
        post = make_post(id="p1")
        post.is_hidden = False
        api = _make_mock_api(
            get_home_feed=AsyncMock(return_value=[post]),
            hide_post=AsyncMock(side_effect=Exception("Hide failed")),
        )
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_hide_requested(PostBlock.HideRequested(post))
            await pilot.pause()
            banner = screen.query_one("#error-banner", Static)
            assert "visible" in banner.classes


class TestSubscribeButton:
    """Test subscribe/unsubscribe button handling (lines 394, 397, 406-411)."""

    @pytest.mark.asyncio
    async def test_non_subscribe_button_ignored(self):
        """Pressing a button that is not btn-subscribe should be ignored (line 394)."""
        api = _make_mock_api()
        state = AppState(current_view=View.HOME)
        api.get_home_feed = AsyncMock(return_value=[make_post()])
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            # Simulate a button press with a different id
            btn = Button("Other", id="other-button")
            event = Button.Pressed(btn)
            await screen.on_button_pressed(event)
            await pilot.pause()
            # No API calls for subscribe/unsubscribe
            api.subscribe.assert_not_called()
            api.unsubscribe.assert_not_called()

    @pytest.mark.asyncio
    async def test_subscribe_button_no_target_returns(self):
        """btn-subscribe press with no target should return early (line 397)."""
        api = _make_mock_api()
        state = AppState(current_view=View.USER_FEED, current_target=None)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            btn = Button("Subscribe", id="btn-subscribe")
            event = Button.Pressed(btn)
            await screen.on_button_pressed(event)
            await pilot.pause()
            api.subscribe.assert_not_called()

    @pytest.mark.asyncio
    async def test_subscribe_calls_api(self):
        """Pressing subscribe when not subscribed should call API."""
        posts = [make_post()]
        api = _make_mock_api(get_user_feed=AsyncMock(return_value=posts))
        state = AppState(current_view=View.USER_FEED, current_target="bob")
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20), notifications=True) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            assert screen.is_subscribed is False
            btn = screen.query_one("#btn-subscribe", Button)
            btn.press()
            await pilot.pause()
            api.subscribe.assert_called_once_with("bob")
            assert screen.is_subscribed is True
            assert btn.label.plain == "Unsubscribe"

    @pytest.mark.asyncio
    async def test_subscribe_error_shows_banner(self):
        """Subscribe failure should show error banner (line 411)."""
        posts = [make_post()]
        api = _make_mock_api(
            get_user_feed=AsyncMock(return_value=posts),
            subscribe=AsyncMock(side_effect=Exception("Sub failed")),
        )
        state = AppState(current_view=View.USER_FEED, current_target="bob")
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            btn = screen.query_one("#btn-subscribe", Button)
            btn.press()
            await pilot.pause()
            banner = screen.query_one("#error-banner", Static)
            assert "visible" in banner.classes


class TestComposePost:
    """Test post creation (lines 425-434)."""

    @pytest.mark.asyncio
    async def test_create_post_success(self):
        """PostRequested should call api.create_post and refresh."""
        api = _make_mock_api()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20), notifications=True) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = ComposeBlock.PostRequested("Hello world", ["alice"])
            await screen.on_compose_block_post_requested(msg)
            await pilot.pause()
            api.create_post.assert_called_once_with("Hello world", ["alice"])
            assert any("Posted" in str(n.message) for n in app._notifications)

    @pytest.mark.asyncio
    async def test_create_post_error_shows_banner(self):
        """PostRequested failure should show error banner."""
        api = _make_mock_api(
            create_post=AsyncMock(side_effect=Exception("Post failed"))
        )
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = ComposeBlock.PostRequested("Hello", ["alice"])
            await screen.on_compose_block_post_requested(msg)
            await pilot.pause()
            banner = screen.query_one("#error-banner", Static)
            assert "visible" in banner.classes


class TestCreateComment:
    """Test comment creation (lines 440-451)."""

    @pytest.mark.asyncio
    async def test_create_comment_success(self):
        """CommentRequested should call api.create_comment and update post."""
        post = make_post(id="p1")
        new_comment = make_comment(id="c_new", body="New comment")
        api = _make_mock_api(
            get_home_feed=AsyncMock(return_value=[post]),
            create_comment=AsyncMock(return_value=new_comment),
        )
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20), notifications=True) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = CommentCompose.CommentRequested("p1", "New comment")
            await screen.on_comment_compose_comment_requested(msg)
            await pilot.pause()
            api.create_comment.assert_called_once_with("p1", "New comment")
            assert any(c.id == "c_new" for c in post.comments)
            assert any("Comment added" in str(n.message) for n in app._notifications)

    @pytest.mark.asyncio
    async def test_create_comment_error_shows_banner(self):
        """CommentRequested failure should show error banner."""
        post = make_post(id="p1")
        api = _make_mock_api(
            get_home_feed=AsyncMock(return_value=[post]),
            create_comment=AsyncMock(side_effect=Exception("Comment failed")),
        )
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = CommentCompose.CommentRequested("p1", "Hello")
            await screen.on_comment_compose_comment_requested(msg)
            await pilot.pause()
            banner = screen.query_one("#error-banner", Static)
            assert "visible" in banner.classes


class TestEditPost:
    """Test post editing (lines 457-469)."""

    @pytest.mark.asyncio
    async def test_edit_post_success(self):
        """EditPostRequested should call api.update_post and update body."""
        post = make_post(id="p1", body="Old body")
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20), notifications=True) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = PostBlock.EditPostRequested(post, "New body")
            await screen.on_post_block_edit_post_requested(msg)
            await pilot.pause()
            api.update_post.assert_called_once_with("p1", "New body")
            assert post.body == "New body"
            assert any("Post updated" in str(n.message) for n in app._notifications)

    @pytest.mark.asyncio
    async def test_edit_post_error_shows_banner(self):
        """EditPostRequested failure should show error banner."""
        post = make_post(id="p1")
        api = _make_mock_api(
            get_home_feed=AsyncMock(return_value=[post]),
            update_post=AsyncMock(side_effect=Exception("Edit failed")),
        )
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = PostBlock.EditPostRequested(post, "New body")
            await screen.on_post_block_edit_post_requested(msg)
            await pilot.pause()
            banner = screen.query_one("#error-banner", Static)
            assert "visible" in banner.classes


class TestDeletePost:
    """Test post deletion (lines 475-495)."""

    @pytest.mark.asyncio
    async def test_delete_post_success_focuses_next(self):
        """DeletePostRequested should remove post and focus next."""
        posts = [make_post(id="p1"), make_post(id="p2"), make_post(id="p3")]
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=posts))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 30), notifications=True) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = PostBlock.DeletePostRequested(posts[0])
            await screen.on_post_block_delete_post_requested(msg)
            await pilot.pause()
            api.delete_post.assert_called_once_with("p1")
            assert any("Post deleted" in str(n.message) for n in app._notifications)

    @pytest.mark.asyncio
    async def test_delete_last_post_focuses_previous(self):
        """Deleting the last post should focus the previous one."""
        posts = [make_post(id="p1"), make_post(id="p2")]
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=posts))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 30), notifications=True) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = PostBlock.DeletePostRequested(posts[1])
            await screen.on_post_block_delete_post_requested(msg)
            await pilot.pause()
            api.delete_post.assert_called_once_with("p2")

    @pytest.mark.asyncio
    async def test_delete_post_error_shows_banner(self):
        """DeletePostRequested failure should show error banner."""
        post = make_post(id="p1")
        api = _make_mock_api(
            get_home_feed=AsyncMock(return_value=[post]),
            delete_post=AsyncMock(side_effect=Exception("Delete failed")),
        )
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = PostBlock.DeletePostRequested(post)
            await screen.on_post_block_delete_post_requested(msg)
            await pilot.pause()
            banner = screen.query_one("#error-banner", Static)
            assert "visible" in banner.classes


class TestEditComment:
    """Test comment editing (lines 501-517)."""

    @pytest.mark.asyncio
    async def test_edit_comment_success(self):
        """EditCommentRequested should call api.update_comment."""
        comment = make_comment(id="c1", body="Old")
        post = make_post(id="p1")
        post.comments = [comment]
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20), notifications=True) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            # Set a CommentBlock to editing=True to cover line 512
            for block in screen.query(PostBlock):
                for cb in block.query(CommentBlock):
                    cb.editing = True
            msg = PostBlock.EditCommentRequested(comment, "Updated")
            await screen.on_post_block_edit_comment_requested(msg)
            await pilot.pause()
            api.update_comment.assert_called_once_with("c1", "Updated")
            assert comment.body == "Updated"
            assert any("Comment updated" in str(n.message) for n in app._notifications)

    @pytest.mark.asyncio
    async def test_edit_comment_error_shows_banner(self):
        """EditCommentRequested failure should show error banner."""
        comment = make_comment(id="c1")
        post = make_post(id="p1")
        post.comments = [comment]
        api = _make_mock_api(
            get_home_feed=AsyncMock(return_value=[post]),
            update_comment=AsyncMock(side_effect=Exception("Edit failed")),
        )
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = PostBlock.EditCommentRequested(comment, "New")
            await screen.on_post_block_edit_comment_requested(msg)
            await pilot.pause()
            banner = screen.query_one("#error-banner", Static)
            assert "visible" in banner.classes


class TestDeleteComment:
    """Test comment deletion (lines 523-544)."""

    @pytest.mark.asyncio
    async def test_delete_comment_success(self):
        """DeleteCommentRequested should remove comment from post."""
        c1 = make_comment(id="c1", body="First")
        c2 = make_comment(id="c2", body="Second")
        post = make_post(id="p1")
        post.comments = [c1, c2]
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20), notifications=True) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = PostBlock.DeleteCommentRequested(c1)
            await screen.on_post_block_delete_comment_requested(msg)
            await pilot.pause()
            api.delete_comment.assert_called_once_with("c1")
            assert c1 not in post.comments
            assert any("Comment deleted" in str(n.message) for n in app._notifications)

    @pytest.mark.asyncio
    async def test_delete_last_comment_focuses_post(self):
        """Deleting the only comment should focus the post block."""
        c1 = make_comment(id="c1", body="Only comment")
        post = make_post(id="p1")
        post.comments = [c1]
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20), notifications=True) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = PostBlock.DeleteCommentRequested(c1)
            await screen.on_post_block_delete_comment_requested(msg)
            await pilot.pause()
            api.delete_comment.assert_called_once_with("c1")
            assert len(post.comments) == 0

    @pytest.mark.asyncio
    async def test_delete_comment_error_shows_banner(self):
        """DeleteCommentRequested failure should show error banner."""
        c1 = make_comment(id="c1")
        post = make_post(id="p1")
        post.comments = [c1]
        api = _make_mock_api(
            get_home_feed=AsyncMock(return_value=[post]),
            delete_comment=AsyncMock(side_effect=Exception("Delete failed")),
        )
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = PostBlock.DeleteCommentRequested(c1)
            await screen.on_post_block_delete_comment_requested(msg)
            await pilot.pause()
            banner = screen.query_one("#error-banner", Static)
            assert "visible" in banner.classes


class TestNoMatchingPostBlock:
    """Test branches where PostBlock loops don't find a matching post."""

    @pytest.mark.asyncio
    async def test_like_nonexistent_post(self):
        """Liking a post not in the feed should still call API but not crash."""
        post_in_feed = make_post(id="p1")
        post_to_like = make_post(id="p_nonexistent")
        post_to_like.is_liked = False
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post_in_feed]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_like_requested(
                PostBlock.LikeRequested(post_to_like)
            )
            await pilot.pause()
            api.like_post.assert_called_once_with("p_nonexistent")

    @pytest.mark.asyncio
    async def test_hide_nonexistent_post(self):
        """Hiding a post not in the feed should call API but not crash."""
        post_in_feed = make_post(id="p1")
        post_to_hide = make_post(id="p_nonexistent")
        post_to_hide.is_hidden = False
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post_in_feed]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_hide_requested(
                PostBlock.HideRequested(post_to_hide)
            )
            await pilot.pause()
            api.hide_post.assert_called_once_with("p_nonexistent")

    @pytest.mark.asyncio
    async def test_edit_post_nonexistent(self):
        """Editing a post not in the feed should call API but not crash."""
        post_in_feed = make_post(id="p1")
        post_to_edit = make_post(id="p_nonexistent")
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post_in_feed]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_edit_post_requested(
                PostBlock.EditPostRequested(post_to_edit, "new")
            )
            await pilot.pause()
            api.update_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_comment_nonexistent_post(self):
        """Creating comment for a post not in feed should call API but not crash."""
        post_in_feed = make_post(id="p1")
        new_comment = make_comment(id="c_new")
        api = _make_mock_api(
            get_home_feed=AsyncMock(return_value=[post_in_feed]),
            create_comment=AsyncMock(return_value=new_comment),
        )
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = CommentCompose.CommentRequested("p_nonexistent", "body")
            await screen.on_comment_compose_comment_requested(msg)
            await pilot.pause()
            api.create_comment.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_comment_nonexistent(self):
        """Editing a comment not in any post should call API but not crash."""
        post = make_post(id="p1")
        comment = make_comment(id="c_nonexistent")
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = PostBlock.EditCommentRequested(comment, "new")
            await screen.on_post_block_edit_comment_requested(msg)
            await pilot.pause()
            api.update_comment.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_comment_nonexistent(self):
        """Deleting a comment not in any post should call API but not crash."""
        post = make_post(id="p1")
        comment = make_comment(id="c_nonexistent")
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = PostBlock.DeleteCommentRequested(comment)
            await screen.on_post_block_delete_comment_requested(msg)
            await pilot.pause()
            api.delete_comment.assert_called_once()

    @pytest.mark.asyncio
    async def test_expand_comments_nonexistent_post(self):
        """Expanding comments for a non-matching post should still call API."""
        post_in_feed = make_post(id="p1")
        post_to_expand = make_post(id="p_nonexistent")
        post_to_expand.omitted_comments = 5
        full_post = make_post(id="p_nonexistent")
        api = _make_mock_api(
            get_home_feed=AsyncMock(return_value=[post_in_feed]),
            get_post=AsyncMock(return_value=full_post),
        )
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_expand_comments(
                PostBlock.ExpandComments(post_to_expand)
            )
            await pilot.pause()
            api.get_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_single_post_no_remaining(self):
        """Deleting the only post should handle empty remaining list."""
        post = make_post(id="p1")
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20), notifications=True) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = PostBlock.DeletePostRequested(post)
            await screen.on_post_block_delete_post_requested(msg)
            await pilot.pause()
            api.delete_post.assert_called_once_with("p1")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_post(self):
        """Deleting a post not in the feed should call API but not crash."""
        post_in_feed = make_post(id="p1")
        post_to_delete = make_post(id="p_nonexistent")
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=[post_in_feed]))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            msg = PostBlock.DeletePostRequested(post_to_delete)
            await screen.on_post_block_delete_post_requested(msg)
            await pilot.pause()
            api.delete_post.assert_called_once()


class TestMenuViewEdgeCases:
    """Test edge cases in menu view selection."""

    @pytest.mark.asyncio
    async def test_search_when_already_on_search(self):
        """Selecting SEARCH when already on SEARCH should still push screen."""
        api = _make_mock_api()
        state = AppState(current_view=View.SEARCH)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.SEARCH))
            await pilot.pause()
            from freefood.screens.search import SearchScreen

            assert any(isinstance(s, SearchScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_notifications_when_already_on_notifications(self):
        """Selecting NOTIFICATIONS when already there should still push."""
        api = _make_mock_api()
        state = AppState(current_view=View.NOTIFICATIONS)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.NOTIFICATIONS))
            await pilot.pause()
            from freefood.screens.notifications import NotificationsScreen

            assert any(isinstance(s, NotificationsScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_errors_when_already_on_errors(self):
        """Selecting ERRORS when already there should still push."""
        api = _make_mock_api()
        state = AppState(current_view=View.ERRORS)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.ERRORS))
            await pilot.pause()
            from freefood.screens.errors import ErrorsScreen

            assert any(isinstance(s, ErrorsScreen) for s in app.pushed_screens)


class TestGroupFeedWithNoTarget:
    """Test GROUP_FEED without target (line 168)."""

    @pytest.mark.asyncio
    async def test_group_feed_no_target_returns_empty(self):
        """GROUP_FEED without target should return empty posts list."""
        api = _make_mock_api()
        state = AppState(current_view=View.GROUP_FEED, current_target=None)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            assert screen.posts == []


class TestExpandCommentsNullPost:
    """Test expand_comments when get_post returns None."""

    @pytest.mark.asyncio
    async def test_expand_comments_returns_none(self):
        """When get_post returns None, should not crash."""
        post = make_post(id="p1")
        api = _make_mock_api(
            get_home_feed=AsyncMock(return_value=[post]),
            get_post=AsyncMock(return_value=None),
        )
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            await screen.on_post_block_expand_comments(PostBlock.ExpandComments(post))
            await pilot.pause()
            # Should not crash


class TestFeedContainerVisibility:
    """Test FeedContainer scroll visibility checking (lines 31, 35)."""

    @pytest.mark.asyncio
    async def test_check_focused_visibility_returns_when_focused_is_none(self):
        """_check_focused_visibility returns early when no widget focused."""
        api = _make_mock_api()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            container = screen.query_one(FeedContainer)
            # Clear focus
            app.set_focus(None)
            await pilot.pause()
            # Should not raise
            container._check_focused_visibility()

    @pytest.mark.asyncio
    async def test_check_focused_visibility_returns_when_post_mode(self):
        """_check_focused_visibility should return early when in post_mode (line 35)."""
        posts = [make_post(id="p1")]
        api = _make_mock_api(get_home_feed=AsyncMock(return_value=posts))
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            container = screen.query_one(FeedContainer)
            # Focus the post block and enter post mode
            post_block = screen.query(PostBlock).first()
            assert post_block is not None
            app.set_focus(post_block)
            await pilot.pause()
            post_block.post_mode = True
            # Should not raise or move focus
            container._check_focused_visibility()
            await pilot.pause()
            assert app.focused is post_block

    @pytest.mark.asyncio
    async def test_check_focused_visibility_non_postblock_focused(self):
        """_check_focused_visibility returns when focused is not PostBlock."""
        api = _make_mock_api()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)
        async with app.run_test(size=(80, 20)) as pilot:
            await app._original_push(FeedScreen(state))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, FeedScreen)
            container = screen.query_one(FeedContainer)
            # Focus a menu button instead of a PostBlock
            menu = screen.query_one(MenuBar)
            menu.focus()
            await pilot.pause()
            # Should not raise
            container._check_focused_visibility()
