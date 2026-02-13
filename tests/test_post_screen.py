"""Tests for PostScreen behavior."""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from textual.app import App
from textual.widgets import Static

from freefood.models import HistoryEntry, Post, User, View
from freefood.screens.post import PostScreen
from freefood.state import AppState
from freefood.widgets.menu import MenuBar
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
        omitted_comments_offset=0,
        omitted_comment_likes=0,
        omitted_likes=0,
        likes=[],
    )


class MockApp(App):
    """App stub for PostScreen tests."""

    def __init__(self, state: AppState | None = None, api: object | None = None):
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


class TestPostScreenWithPost:
    """Tests for PostScreen when post is provided directly."""

    @pytest.mark.asyncio
    async def test_renders_provided_post(self):
        """PostScreen should render the post passed in the constructor."""
        post = make_post(body="Hello from post screen")
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post=post))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            assert screen.query(PostBlock).first() is not None


class TestPostScreenLoadFromAPI:
    """Tests for PostScreen when loading post from API."""

    @pytest.mark.asyncio
    async def test_loads_post_from_api_by_id(self):
        """PostScreen should call api.get_post when post_id is provided."""
        post = make_post(id="p42", body="Loaded from API")
        api = AsyncMock()
        api.get_post = AsyncMock(return_value=post)

        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post_id="p42"))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            api.get_post.assert_called_once_with("p42")
            assert screen.query(PostBlock).first() is not None

    @pytest.mark.asyncio
    async def test_shows_error_when_api_is_none(self):
        """PostScreen should show error when api is None."""
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=None)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post_id="p1"))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            error = screen.query_one(".error", Static)
            assert "Not connected" in str(error.render())

    @pytest.mark.asyncio
    async def test_shows_error_when_post_id_is_none(self):
        """PostScreen should show error when post and post_id are both None."""
        api = AsyncMock()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            error = screen.query_one(".error", Static)
            assert "Missing post id" in str(error.render())

    @pytest.mark.asyncio
    async def test_shows_error_when_api_raises(self):
        """PostScreen should show error when api.get_post raises."""
        api = AsyncMock()
        api.get_post = AsyncMock(side_effect=Exception("Network fail"))

        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post_id="p1"))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            error = screen.query_one(".error", Static)
            assert "Network fail" in str(error.render())


class TestPostScreenStateFallback:
    """Tests for state property fallback."""

    @pytest.mark.asyncio
    async def test_state_falls_back_to_app_state(self):
        """PostScreen.state should fall back to self.app.state when _state is None."""
        post = make_post()
        app_state = AppState(current_view=View.HOME)
        app = MockApp(state=app_state)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state=None, post=post))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            # The screen state should be the app's state
            assert screen.state is app_state


class TestPostScreenFocus:
    """Tests for focus actions."""

    @pytest.mark.asyncio
    async def test_action_focus_menu(self):
        """action_focus_menu should focus the menu bar."""
        from textual.widgets import Button

        post = make_post()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post=post))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            screen.action_focus_menu()
            await pilot.pause()

            focused = app.focused
            assert isinstance(focused, Button)

    @pytest.mark.asyncio
    async def test_action_focus_post(self):
        """action_focus_post should focus the PostBlock."""
        post = make_post()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post=post))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            screen.action_focus_post()
            await pilot.pause()

            focused = app.focused
            assert isinstance(focused, PostBlock)

    @pytest.mark.asyncio
    async def test_action_focus_post_focuses_post_block(self):
        """action_focus_post should focus the PostBlock when present."""
        post = make_post()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post=post))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            # First focus the menu, then use action_focus_post to refocus
            screen.action_focus_menu()
            await pilot.pause()
            screen.action_focus_post()
            await pilot.pause()

            focused = app.focused
            assert isinstance(focused, PostBlock)


class TestPostScreenRefresh:
    """Tests for the refresh action."""

    @pytest.mark.asyncio
    async def test_action_refresh_reloads_content(self):
        """action_refresh should trigger refresh_content via worker."""
        post = make_post()
        api = AsyncMock()
        api.get_post = AsyncMock(return_value=post)

        state = AppState(current_view=View.HOME)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post_id="p1"))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)

            # Reset the post so refresh fetches again
            screen.post = None
            screen.action_refresh()
            await pilot.pause()

            assert api.get_post.call_count == 2


class TestPostScreenMenuNavigation:
    """Tests for menu bar view selection navigation."""

    @pytest.mark.asyncio
    async def test_selecting_search_navigates(self):
        """Selecting SEARCH view should push SearchScreen."""
        post = make_post()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post=post))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.SEARCH))
            await pilot.pause()

            from freefood.screens.search import SearchScreen

            assert any(isinstance(s, SearchScreen) for s in app.pushed_screens)
            assert state.current_view == View.SEARCH

    @pytest.mark.asyncio
    async def test_selecting_notifications_navigates(self):
        """Selecting NOTIFICATIONS view should push NotificationsScreen."""
        post = make_post()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post=post))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.NOTIFICATIONS))
            await pilot.pause()

            from freefood.screens.notifications import NotificationsScreen

            assert any(isinstance(s, NotificationsScreen) for s in app.pushed_screens)
            assert state.current_view == View.NOTIFICATIONS

    @pytest.mark.asyncio
    async def test_selecting_errors_navigates(self):
        """Selecting ERRORS view should push ErrorsScreen."""
        post = make_post()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post=post))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.ERRORS))
            await pilot.pause()

            from freefood.screens.errors import ErrorsScreen

            assert any(isinstance(s, ErrorsScreen) for s in app.pushed_screens)
            assert state.current_view == View.ERRORS

    @pytest.mark.asyncio
    async def test_selecting_home_navigates_to_feed(self):
        """Selecting HOME view should push FeedScreen."""
        post = make_post()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post=post))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.HOME))
            await pilot.pause()

            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_selecting_directs_navigates_to_feed(self):
        """Selecting DIRECTS view should push FeedScreen."""
        post = make_post()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post=post))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.DIRECTS))
            await pilot.pause()

            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)
            assert state.current_view == View.DIRECTS

    @pytest.mark.asyncio
    async def test_view_selected_stops_message(self):
        """on_menu_bar_view_selected should stop the message."""
        post = make_post()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post=post))
            await pilot.pause()

            screen = app.screen
            msg = MenuBar.ViewSelected(View.HOME)
            screen.on_menu_bar_view_selected(msg)
            await pilot.pause()
            assert msg._stop_propagation


class TestPostScreenBackNavigation:
    """Tests for back navigation via menu bar."""

    @pytest.mark.asyncio
    async def test_back_with_no_history_notifies(self):
        """Back with empty history should show 'No history' notification."""
        post = make_post()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state)

        async with app.run_test(size=(80, 20), notifications=True) as pilot:
            await app.push_screen(PostScreen(state, post=post))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)

            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            assert any("No history" in str(n.message) for n in app._notifications)

    @pytest.mark.asyncio
    async def test_back_to_home_pushes_feed_screen(self):
        """Back to HOME should push FeedScreen."""
        post = make_post()
        state = AppState(current_view=View.HOME)
        state.history.append(
            HistoryEntry(view=View.HOME, target=None, scroll_position=0)
        )
        app = MockApp(state=state)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post=post))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)
            assert state.current_view == View.HOME

    @pytest.mark.asyncio
    async def test_back_to_search_pushes_search_screen(self):
        """Back to SEARCH should push SearchScreen."""
        post = make_post()
        state = AppState(current_view=View.HOME)
        state.history.append(
            HistoryEntry(view=View.SEARCH, target=None, scroll_position=0, query="test")
        )
        app = MockApp(state=state)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post=post))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            from freefood.screens.search import SearchScreen

            assert any(isinstance(s, SearchScreen) for s in app.pushed_screens)
            assert state.current_view == View.SEARCH
            assert state.search_query == "test"

    @pytest.mark.asyncio
    async def test_back_to_notifications_pushes_notifications_screen(self):
        """Back to NOTIFICATIONS should push NotificationsScreen."""
        post = make_post()
        state = AppState(current_view=View.HOME)
        state.history.append(
            HistoryEntry(view=View.NOTIFICATIONS, target=None, scroll_position=0)
        )
        app = MockApp(state=state)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post=post))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            from freefood.screens.notifications import NotificationsScreen

            assert any(isinstance(s, NotificationsScreen) for s in app.pushed_screens)
            assert state.current_view == View.NOTIFICATIONS

    @pytest.mark.asyncio
    async def test_back_restores_target(self):
        """Back should restore current_target from history entry."""
        post = make_post()
        state = AppState(current_view=View.HOME)
        state.history.append(
            HistoryEntry(view=View.USER_FEED, target="bob", scroll_position=0)
        )
        app = MockApp(state=state)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post=post))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            assert state.current_view == View.USER_FEED
            assert state.current_target == "bob"

    @pytest.mark.asyncio
    async def test_back_without_query_does_not_set_search_query(self):
        """Back to HOME should not modify search_query if entry has no query."""
        post = make_post()
        state = AppState(current_view=View.HOME, search_query="old")
        state.history.append(
            HistoryEntry(view=View.HOME, target=None, scroll_position=0)
        )
        app = MockApp(state=state)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post=post))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, PostScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            # query should remain "old" since entry.query is None
            assert state.search_query == "old"

    @pytest.mark.asyncio
    async def test_back_stops_message(self):
        """on_menu_bar_back_requested should stop the message."""
        post = make_post()
        state = AppState(current_view=View.HOME)
        app = MockApp(state=state)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(PostScreen(state, post=post))
            await pilot.pause()

            screen = app.screen
            msg = MenuBar.BackRequested()
            screen.on_menu_bar_back_requested(msg)
            await pilot.pause()
            assert msg._stop_propagation
