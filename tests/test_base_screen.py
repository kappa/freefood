"""Tests for BaseScreen error banner support and navigation helpers."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static

from freefood.models import HistoryEntry, View
from freefood.screens.base import BaseScreen
from freefood.state import AppState
from freefood.widgets.menu import MenuBar


class ScreenWithBanner(BaseScreen):
    """Test screen that includes an error-banner widget."""

    CSS = BaseScreen.ERROR_BANNER_CSS

    def compose(self) -> ComposeResult:
        yield Static("", id="error-banner")
        yield Static("Main content", id="main")


class ScreenWithoutBanner(BaseScreen):
    """Test screen that does NOT include an error-banner widget."""

    def compose(self) -> ComposeResult:
        yield Static("Main content", id="main")


class TestShowError:
    """Tests for BaseScreen.show_error."""

    @pytest.mark.asyncio
    async def test_show_error_displays_message(self):
        """show_error should display the message in the error banner."""
        app = App()
        async with app.run_test() as pilot:
            screen = ScreenWithBanner()
            await app.push_screen(screen)
            await pilot.pause()

            screen.show_error("Something went wrong")
            await pilot.pause()

            banner = screen.query_one("#error-banner", Static)
            assert "Something went wrong" in str(banner.render())
            assert banner.has_class("visible")

    @pytest.mark.asyncio
    async def test_show_error_with_exception(self):
        """show_error with exception should include exception text."""
        app = App()
        async with app.run_test() as pilot:
            screen = ScreenWithBanner()
            await app.push_screen(screen)
            await pilot.pause()

            screen.show_error("Failed", Exception("timeout"))
            await pilot.pause()

            banner = screen.query_one("#error-banner", Static)
            rendered = str(banner.render())
            assert "Failed" in rendered
            assert "timeout" in rendered
            assert banner.has_class("visible")

    @pytest.mark.asyncio
    async def test_show_error_without_banner_does_not_crash(self):
        """show_error should silently pass when no error-banner exists."""
        app = App()
        async with app.run_test() as pilot:
            screen = ScreenWithoutBanner()
            await app.push_screen(screen)
            await pilot.pause()

            # Should not raise any exception
            screen.show_error("No banner here")
            await pilot.pause()


class TestHideError:
    """Tests for BaseScreen.hide_error."""

    @pytest.mark.asyncio
    async def test_hide_error_removes_visible_class(self):
        """hide_error should remove the visible class from the error banner."""
        app = App()
        async with app.run_test() as pilot:
            screen = ScreenWithBanner()
            await app.push_screen(screen)
            await pilot.pause()

            # First show an error
            screen.show_error("Visible error")
            await pilot.pause()

            banner = screen.query_one("#error-banner", Static)
            assert banner.has_class("visible")

            # Now hide it
            screen.hide_error()
            await pilot.pause()

            assert not banner.has_class("visible")

    @pytest.mark.asyncio
    async def test_hide_error_without_banner_does_not_crash(self):
        """hide_error should silently pass when no error-banner exists."""
        app = App()
        async with app.run_test() as pilot:
            screen = ScreenWithoutBanner()
            await app.push_screen(screen)
            await pilot.pause()

            # Should not raise any exception
            screen.hide_error()
            await pilot.pause()


class MinimalScreen(BaseScreen):
    """Minimal screen for testing BaseScreen navigation helpers."""

    def compose(self):
        yield MenuBar(View.HOME)


class NavMockApp(App):
    def __init__(self, state=None):
        super().__init__()
        self.state = state or AppState()
        self.pushed_screens: list = []
        self._original_push = None

    async def on_mount(self):
        self._original_push = self.push_screen

        def tracking_push(screen, *args, **kwargs):
            self.pushed_screens.append(screen)
            return self._original_push(screen, *args, **kwargs)

        self.push_screen = tracking_push


class TestPushScreenForView:
    """Tests for push_screen_for_view helper."""

    @pytest.mark.asyncio
    async def test_push_feed_screen_for_home(self):
        app = NavMockApp()
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.push_screen_for_view(View.HOME)
            await pilot.pause()
            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_push_search_screen(self):
        app = NavMockApp()
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.push_screen_for_view(View.SEARCH)
            await pilot.pause()
            from freefood.screens.search import SearchScreen

            assert any(isinstance(s, SearchScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_push_notifications_screen(self):
        app = NavMockApp()
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.push_screen_for_view(View.NOTIFICATIONS)
            await pilot.pause()
            from freefood.screens.notifications import NotificationsScreen

            assert any(isinstance(s, NotificationsScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_push_errors_screen(self):
        app = NavMockApp()
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.push_screen_for_view(View.ERRORS)
            await pilot.pause()
            from freefood.screens.errors import ErrorsScreen

            assert any(isinstance(s, ErrorsScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_push_theme_screen(self):
        app = NavMockApp()
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.push_screen_for_view(View.THEME)
            await pilot.pause()
            from freefood.screens.theme import ThemeScreen

            assert any(isinstance(s, ThemeScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_push_feed_screen_for_directs(self):
        app = NavMockApp()
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.push_screen_for_view(View.DIRECTS)
            await pilot.pause()
            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_push_feed_screen_for_user_feed(self):
        app = NavMockApp()
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.push_screen_for_view(View.USER_FEED)
            await pilot.pause()
            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_push_feed_screen_for_group_feed(self):
        app = NavMockApp()
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.push_screen_for_view(View.GROUP_FEED)
            await pilot.pause()
            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)


class TestNavigateBack:
    """Tests for navigate_back helper."""

    @pytest.mark.asyncio
    async def test_navigate_back_pops_screen(self):
        state = AppState()
        state.history.append(
            HistoryEntry(view=View.HOME, target=None, scroll_position=0)
        )
        app = NavMockApp(state=state)
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            stack_size_before = len(app.screen_stack)
            result = screen.navigate_back()
            assert result is True
            await pilot.pause()
            # Back should pop (shrink stack), not push (grow stack)
            assert len(app.screen_stack) < stack_size_before
            assert state.current_view == View.HOME

    @pytest.mark.asyncio
    async def test_navigate_back_restores_search_query(self):
        state = AppState()
        state.history.append(
            HistoryEntry(view=View.SEARCH, target=None, scroll_position=0, query="test")
        )
        app = NavMockApp(state=state)
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.navigate_back()
            await pilot.pause()
            assert state.search_query == "test"

    @pytest.mark.asyncio
    async def test_navigate_back_restores_target(self):
        state = AppState()
        state.history.append(
            HistoryEntry(view=View.USER_FEED, target="bob", scroll_position=0)
        )
        app = NavMockApp(state=state)
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.navigate_back()
            await pilot.pause()
            assert state.current_target == "bob"

    @pytest.mark.asyncio
    async def test_navigate_back_empty_history_returns_false(self):
        state = AppState()
        app = NavMockApp(state=state)
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            result = screen.navigate_back()
            assert result is False

    @pytest.mark.asyncio
    async def test_navigate_back_does_not_overwrite_query_when_none(self):
        state = AppState(search_query="existing")
        state.history.append(
            HistoryEntry(view=View.HOME, target=None, scroll_position=0)
        )
        app = NavMockApp(state=state)
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.navigate_back()
            await pilot.pause()
            assert state.search_query == "existing"
