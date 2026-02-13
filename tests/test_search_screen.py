"""Tests for SearchScreen behavior."""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from textual.app import App
from textual.widgets import Button, Input, Static

from freefood.models import HistoryEntry, Post, User, View
from freefood.screens.search import SearchScreen
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


class FakeAPI:
    """Minimal API stub for search."""

    def __init__(self, posts: list[Post]) -> None:
        self.posts = posts
        self.calls: list[str] = []

    async def search(self, query: str, offset: int = 0, limit: int = 30) -> list[Post]:
        self.calls.append(query)
        return self.posts


class TestSearchScreen:
    """Tests for SearchScreen."""

    @pytest.mark.asyncio
    async def test_empty_state_when_no_query(self):
        """SearchScreen should show empty state when query is blank."""
        from textual.app import App
        from textual.widgets import Static

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI([])
                self.state = AppState(current_view=View.SEARCH)

            def on_mount(self) -> None:
                self.push_screen(SearchScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, SearchScreen)
            screen.query_one("#search-empty", Static)

    @pytest.mark.asyncio
    async def test_submit_query_calls_api_and_updates_state(self):
        """Submitting a search should call API and show results."""
        from textual.app import App
        from textual.widgets import Input

        posts = [make_post(id="p1", body="Hello world")]
        api = FakeAPI(posts)

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = api
                self.state = AppState(current_view=View.SEARCH)

            def on_mount(self) -> None:
                self.push_screen(SearchScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, SearchScreen)
            search_input = screen.query_one("#search-input", Input)
            search_input.value = "hello"
            search_input.focus()
            await pilot.pause()

            await pilot.press("enter")
            await pilot.pause()

            assert api.calls == ["hello"]
            assert screen.state.search_query == "hello"
            assert screen.query(PostBlock).first() is not None

    @pytest.mark.asyncio
    async def test_escape_clears_query_and_results(self):
        """Escape should clear query and reset results to empty state."""
        from textual.app import App
        from textual.widgets import Input, Static

        posts = [make_post(id="p1", body="Hello world")]
        api = FakeAPI(posts)

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = api
                self.state = AppState(current_view=View.SEARCH)

            def on_mount(self) -> None:
                self.push_screen(SearchScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, SearchScreen)
            search_input = screen.query_one("#search-input", Input)
            search_input.value = "hello"
            search_input.focus()
            await pilot.pause()

            await pilot.press("enter")
            await pilot.pause()

            await pilot.press("escape")
            await pilot.pause()

            assert search_input.value == ""
            screen.query_one("#search-empty", Static)


class MockApp(App):
    """App stub with screen tracking for navigation tests."""

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


class TestSearchStateFallback:
    """Tests for state property fallback."""

    @pytest.mark.asyncio
    async def test_state_falls_back_to_app_state(self):
        """State should fall back to app.state when _state is None."""
        api = FakeAPI([])
        app_state = AppState(current_view=View.SEARCH)
        app = MockApp(state=app_state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state=None))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            assert screen.state is app_state


class TestSearchAutoSearch:
    """Tests for auto-search on mount with existing query."""

    @pytest.mark.asyncio
    async def test_auto_searches_when_query_present(self):
        """SearchScreen should auto-search when state has a search_query."""
        posts = [make_post(id="p1", body="Hello world")]
        api = FakeAPI(posts)
        state = AppState(current_view=View.SEARCH, search_query="hello")
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            assert api.calls == ["hello"]
            assert screen.query(PostBlock).first() is not None


class TestSearchNoResults:
    """Tests for no results state."""

    @pytest.mark.asyncio
    async def test_shows_no_results_message(self):
        """SearchScreen should show no results message when API returns empty."""
        api = FakeAPI([])
        state = AppState(current_view=View.SEARCH)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            search_input = screen.query_one("#search-input", Input)
            search_input.value = "nonexistent"
            search_input.focus()
            await pilot.pause()

            await pilot.press("enter")
            await pilot.pause()

            # Should show "No results found"
            container = screen.query_one("#search-results")
            statics = container.query(Static)
            texts = [str(s.render()) for s in statics]
            assert any("No results" in t for t in texts)


class TestSearchErrorHandling:
    """Tests for error handling in search."""

    @pytest.mark.asyncio
    async def test_shows_error_when_api_is_none(self):
        """Should show error when api is None."""
        state = AppState(current_view=View.SEARCH)
        app = MockApp(state=state, api=None)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            search_input = screen.query_one("#search-input", Input)
            search_input.value = "test"
            search_input.focus()
            await pilot.pause()

            await pilot.press("enter")
            await pilot.pause()

            error = screen.query_one(".error", Static)
            assert "Not connected" in str(error.render())

    @pytest.mark.asyncio
    async def test_shows_error_when_api_raises(self):
        """Should show error when api.search raises."""
        api = AsyncMock()
        api.search = AsyncMock(side_effect=Exception("Search failed"))
        state = AppState(current_view=View.SEARCH)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            search_input = screen.query_one("#search-input", Input)
            search_input.value = "test"
            search_input.focus()
            await pilot.pause()

            await pilot.press("enter")
            await pilot.pause()

            error = screen.query_one(".error", Static)
            assert "Search failed" in str(error.render())


class TestSearchRefresh:
    """Tests for the refresh action."""

    @pytest.mark.asyncio
    async def test_action_refresh_re_runs_search(self):
        """action_refresh should re-run the search."""
        posts = [make_post()]
        api = FakeAPI(posts)
        state = AppState(current_view=View.SEARCH)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            search_input = screen.query_one("#search-input", Input)
            search_input.value = "test"
            search_input.focus()
            await pilot.pause()

            await pilot.press("enter")
            await pilot.pause()

            assert len(api.calls) == 1

            screen.action_refresh()
            await pilot.pause()

            assert len(api.calls) == 2


class TestSearchClearOrFocusMenu:
    """Tests for the clear_or_focus_menu action."""

    @pytest.mark.asyncio
    async def test_escape_with_empty_input_focuses_menu(self):
        """Escape with empty input should focus the menu bar."""
        api = FakeAPI([])
        state = AppState(current_view=View.SEARCH)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            search_input = screen.query_one("#search-input", Input)
            assert search_input.value == ""

            # Focus the input
            search_input.focus()
            await pilot.pause()

            # Press escape -- should focus menu since input is empty
            screen.action_clear_or_focus_menu()
            await pilot.pause()

            focused = app.focused
            assert isinstance(focused, Button)


class TestSearchButtonPressed:
    """Tests for button pressed events."""

    @pytest.mark.asyncio
    async def test_clear_button_clears_input(self):
        """Clear button should clear input and show empty state."""
        posts = [make_post()]
        api = FakeAPI(posts)
        state = AppState(current_view=View.SEARCH)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            search_input = screen.query_one("#search-input", Input)
            search_input.value = "test"
            search_input.focus()
            await pilot.pause()

            await pilot.press("enter")
            await pilot.pause()

            assert screen.state.search_query == "test"

            # Press clear button
            clear_btn = screen.query_one("#clear-search", Button)
            clear_btn.press()
            await pilot.pause()

            assert search_input.value == ""
            assert screen.state.search_query == ""


class TestSearchMenuNavigation:
    """Tests for menu bar view selection navigation."""

    @pytest.mark.asyncio
    async def test_selecting_search_refreshes(self):
        """Selecting SEARCH view should refresh results."""
        api = FakeAPI([])
        state = AppState(current_view=View.SEARCH)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)

            count_before = len(app.pushed_screens)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.SEARCH))
            await pilot.pause()

            # Should stay on same screen (no new push)
            assert len(app.pushed_screens) == count_before

    @pytest.mark.asyncio
    async def test_selecting_notifications_navigates(self):
        """Selecting NOTIFICATIONS view should push NotificationsScreen."""
        api = FakeAPI([])
        state = AppState(current_view=View.SEARCH)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.NOTIFICATIONS))
            await pilot.pause()

            from freefood.screens.notifications import NotificationsScreen

            assert any(isinstance(s, NotificationsScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_selecting_errors_navigates(self):
        """Selecting ERRORS view should push ErrorsScreen."""
        api = FakeAPI([])
        state = AppState(current_view=View.SEARCH)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.ERRORS))
            await pilot.pause()

            from freefood.screens.errors import ErrorsScreen

            assert any(isinstance(s, ErrorsScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_selecting_home_pushes_feed_screen(self):
        """Selecting HOME view should push FeedScreen."""
        api = FakeAPI([])
        state = AppState(current_view=View.SEARCH)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.HOME))
            await pilot.pause()

            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_selecting_directs_pushes_feed_screen(self):
        """Selecting DIRECTS view should push FeedScreen."""
        api = FakeAPI([])
        state = AppState(current_view=View.SEARCH)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.DIRECTS))
            await pilot.pause()

            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_view_selected_stops_message(self):
        """on_menu_bar_view_selected should stop the message."""
        api = FakeAPI([])
        state = AppState(current_view=View.SEARCH)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            msg = MenuBar.ViewSelected(View.HOME)
            screen.on_menu_bar_view_selected(msg)
            await pilot.pause()
            assert msg._stop_propagation


class TestSearchBackNavigation:
    """Tests for back navigation via menu bar."""

    @pytest.mark.asyncio
    async def test_back_with_no_history_notifies(self):
        """Back with empty history should show notification."""
        api = FakeAPI([])
        state = AppState(current_view=View.SEARCH)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20), notifications=True) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            assert len(app._notifications) > 0
            assert any("No history" in str(n.message) for n in app._notifications)

    @pytest.mark.asyncio
    async def test_back_to_home_pushes_feed_screen(self):
        """Back to HOME should push FeedScreen."""
        api = FakeAPI([])
        state = AppState(current_view=View.SEARCH)
        state.history.append(
            HistoryEntry(view=View.HOME, target=None, scroll_position=0)
        )
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)
            assert state.current_view == View.HOME

    @pytest.mark.asyncio
    async def test_back_to_search_pushes_search_screen(self):
        """Back to SEARCH should push a new SearchScreen."""
        posts = [make_post()]
        api = FakeAPI(posts)
        state = AppState(current_view=View.SEARCH)
        state.history.append(
            HistoryEntry(view=View.SEARCH, target=None, scroll_position=0, query="old")
        )
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            assert state.current_view == View.SEARCH
            assert state.search_query == "old"
            assert any(
                isinstance(s, SearchScreen) and s is not screen
                for s in app.pushed_screens
            )

    @pytest.mark.asyncio
    async def test_back_to_notifications_pushes_notifications_screen(self):
        """Back to NOTIFICATIONS should push NotificationsScreen."""
        api = FakeAPI([])
        state = AppState(current_view=View.SEARCH)
        state.history.append(
            HistoryEntry(view=View.NOTIFICATIONS, target=None, scroll_position=0)
        )
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            from freefood.screens.notifications import NotificationsScreen

            assert any(isinstance(s, NotificationsScreen) for s in app.pushed_screens)
            assert state.current_view == View.NOTIFICATIONS

    @pytest.mark.asyncio
    async def test_back_restores_target(self):
        """Back should restore current_target from history entry."""
        api = FakeAPI([])
        state = AppState(current_view=View.SEARCH)
        state.history.append(
            HistoryEntry(view=View.USER_FEED, target="bob", scroll_position=0)
        )
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)
            assert state.current_view == View.USER_FEED
            assert state.current_target == "bob"

    @pytest.mark.asyncio
    async def test_back_with_query_none_does_not_overwrite(self):
        """Back entry with query=None should not modify search_query."""
        api = FakeAPI([])
        state = AppState(current_view=View.SEARCH, search_query="existing")
        state.history.append(
            HistoryEntry(view=View.HOME, target=None, scroll_position=0, query=None)
        )
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            assert state.search_query == "existing"

    @pytest.mark.asyncio
    async def test_back_stops_message(self):
        """on_menu_bar_back_requested should stop the message."""
        api = FakeAPI([])
        state = AppState(current_view=View.SEARCH)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            msg = MenuBar.BackRequested()
            screen.on_menu_bar_back_requested(msg)
            await pilot.pause()
            assert msg._stop_propagation


class TestSearchRefreshEmptyQuery:
    """Tests for refresh with empty query."""

    @pytest.mark.asyncio
    async def test_refresh_empty_query_shows_empty_state(self):
        """Refreshing with empty query should show empty state."""
        api = FakeAPI([])
        state = AppState(current_view=View.SEARCH)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(SearchScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SearchScreen)
            # Input is empty by default
            screen.action_refresh()
            await pilot.pause()

            screen.query_one("#search-empty", Static)
