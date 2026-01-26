"""Tests for FeedScreen behavior."""

from datetime import datetime

import pytest

from freefood.models import Post, User, View, Comment
from freefood.screens.feed import FeedScreen
from freefood.state import AppState
from freefood.widgets.post import PostBlock, CommentBlock


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
        comments=[],
        omitted_comments=0,
        omitted_comments_offset=0,
        omitted_comment_likes=0,
        omitted_likes=0,
        likes=[],
    )


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

            # Press Up - currently changes selection (this test verifies current broken behavior)
            # The test should FAIL once we check that Up moves to previous post
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
            assert app.focused is post_blocks[1], f"Expected post_blocks[1], got {app.focused}"

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

            assert app.focused is post_blocks[0], f"Setup: expected post_blocks[0], got {app.focused}"

            # Press Tab - should move to next post
            await pilot.press("tab")
            await pilot.pause()

            # Selection should be on second post
            assert app.focused is post_blocks[1], f"Tab should move to next post, got {app.focused}"

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

            assert app.focused is post_blocks[1], f"Setup: expected post_blocks[1], got {app.focused}"

            # Press Shift+Tab - should move to previous post
            await pilot.press("shift+tab")
            await pilot.pause()

            # Selection should be on first post
            assert app.focused is post_blocks[0], f"Shift+Tab should move to previous post, got {app.focused}"


class TestAutoSelectionOnScroll:
    """Tests for auto-moving selection when focused post scrolls out of view."""

    @pytest.mark.asyncio
    async def test_selection_moves_when_focused_post_scrolls_out_of_view(self):
        """When focused post scrolls completely out of view, selection moves to visible post."""
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
            assert isinstance(focused, PostBlock), f"Focus should be on a PostBlock, got {type(focused)}"


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

        group = make_user(id="g1", username="news", screen_name="News Group", user_type="group")
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
                self.state = AppState(current_view=View.GROUP_FEED, current_target="news")

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
