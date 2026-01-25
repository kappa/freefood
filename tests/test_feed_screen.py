"""Tests for FeedScreen behavior."""

from datetime import datetime

import pytest

from freefood.models import Post, User
from freefood.screens.feed import FeedScreen
from freefood.state import AppState
from freefood.widgets.post import PostBlock


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

        async with TestApp().run_test(size=(80, 20)) as pilot:
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
