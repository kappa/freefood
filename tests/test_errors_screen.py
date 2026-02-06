"""Tests for ErrorsScreen."""

from unittest.mock import patch

import pytest
from textual.app import App

from freefood.logging import clear_errors, log_error
from freefood.models import HistoryEntry, View
from freefood.screens.errors import ErrorsScreen
from freefood.state import AppState
from freefood.widgets.menu import MenuBar


class MockApp(App):
    def __init__(self, state: AppState | None = None) -> None:
        super().__init__()
        self.state = state or AppState()
        self.pushed_screens: list = []
        self._original_push = None

    async def on_mount(self) -> None:
        # Track screens pushed via push_screen
        self._original_push = self.push_screen

        def tracking_push(screen, *args, **kwargs):
            self.pushed_screens.append(screen)
            return self._original_push(screen, *args, **kwargs)

        self.push_screen = tracking_push  # type: ignore[assignment]


@pytest.mark.asyncio
async def test_errors_screen_displays_errors():
    """ErrorsScreen should render logged errors."""
    clear_errors()
    log_error("UI Test Error", Exception("UI Exception"))

    app = MockApp()
    async with app.run_test() as pilot:
        await app.push_screen(ErrorsScreen())

        # Check if error message is rendered
        assert pilot.app.screen.query(".error-message")
        assert pilot.app.screen.query(".error-exception")

        # Verify specific content
        static_msg = pilot.app.screen.query_one(".error-message")
        assert "UI Test Error" in str(static_msg.render())


@pytest.mark.asyncio
async def test_errors_screen_clear_action():
    """Pressing 'c' should clear errors."""
    clear_errors()
    log_error("Error to clear")

    app = MockApp()
    async with app.run_test() as pilot:
        await app.push_screen(ErrorsScreen())
        assert pilot.app.screen.query(".error-entry")

        # Press 'c' to clear
        await pilot.press("c")

        # Should now show empty state
        assert not pilot.app.screen.query(".error-entry")
        assert pilot.app.screen.query_one("#errors-empty")


class TestErrorsScreenFocusMenu:
    """Tests for the focus_menu action."""

    @pytest.mark.asyncio
    async def test_escape_focuses_menu(self):
        """Pressing escape should focus the menu bar's current view button."""
        clear_errors()
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(ErrorsScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ErrorsScreen)

            # Trigger the focus_menu action
            screen.action_focus_menu()
            await pilot.pause()

            # The errors button should be focused (since View.ERRORS is current)
            from textual.widgets import Button

            focused = app.focused
            assert isinstance(focused, Button)


class TestErrorsScreenRefresh:
    """Tests for the refresh action."""

    @pytest.mark.asyncio
    async def test_f5_calls_action_refresh(self):
        """Pressing F5 should trigger the refresh action."""
        clear_errors()
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(ErrorsScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ErrorsScreen)

            with patch.object(screen, "action_refresh") as mock_refresh:
                await pilot.press("f5")
                await pilot.pause()

                mock_refresh.assert_called_once()


class TestErrorsScreenMenuNavigation:
    """Tests for menu bar view selection navigation."""

    @pytest.mark.asyncio
    async def test_selecting_errors_view_is_noop(self):
        """Selecting ERRORS view from menu should do nothing (already there)."""
        clear_errors()
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(ErrorsScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ErrorsScreen)

            # Send ERRORS view selection - should be a no-op
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.ERRORS))
            await pilot.pause()

            # Should still be on ErrorsScreen
            assert isinstance(app.screen, ErrorsScreen)

    @pytest.mark.asyncio
    async def test_selecting_home_view_navigates(self):
        """Selecting HOME view should push FeedScreen."""
        clear_errors()
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(ErrorsScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ErrorsScreen)

            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.HOME))
            await pilot.pause()

            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_selecting_search_view_navigates(self):
        """Selecting SEARCH view should push SearchScreen."""
        clear_errors()
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(ErrorsScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ErrorsScreen)

            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.SEARCH))
            await pilot.pause()

            from freefood.screens.search import SearchScreen

            assert any(isinstance(s, SearchScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_selecting_notifications_view_navigates(self):
        """Selecting NOTIFICATIONS view should push NotificationsScreen."""
        clear_errors()
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(ErrorsScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ErrorsScreen)

            screen.on_menu_bar_view_selected(
                MenuBar.ViewSelected(View.NOTIFICATIONS)
            )
            await pilot.pause()

            from freefood.screens.notifications import NotificationsScreen

            assert any(
                isinstance(s, NotificationsScreen) for s in app.pushed_screens
            )


class TestErrorsScreenBackNavigation:
    """Tests for back navigation via menu bar."""

    @pytest.mark.asyncio
    async def test_back_with_no_history_notifies(self):
        """Back with empty history should show 'No history' notification."""
        clear_errors()
        state = AppState()
        app = MockApp(state=state)
        async with app.run_test(notifications=True) as pilot:
            await app.push_screen(ErrorsScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ErrorsScreen)

            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            # Check notification was shown
            assert len(app._notifications) > 0
            assert any("No history" in str(n.message) for n in app._notifications)

    @pytest.mark.asyncio
    async def test_back_to_home_view(self):
        """Back to HOME should push FeedScreen."""
        clear_errors()
        state = AppState()
        state.history.append(
            HistoryEntry(view=View.HOME, target=None, scroll_position=0)
        )
        app = MockApp(state=state)
        async with app.run_test() as pilot:
            await app.push_screen(ErrorsScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ErrorsScreen)

            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)
            assert state.current_view == View.HOME

    @pytest.mark.asyncio
    async def test_back_to_search_view(self):
        """Back to SEARCH should push SearchScreen."""
        clear_errors()
        state = AppState()
        state.history.append(
            HistoryEntry(view=View.SEARCH, target=None, scroll_position=0)
        )
        app = MockApp(state=state)
        async with app.run_test() as pilot:
            await app.push_screen(ErrorsScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ErrorsScreen)

            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            from freefood.screens.search import SearchScreen

            assert any(isinstance(s, SearchScreen) for s in app.pushed_screens)
            assert state.current_view == View.SEARCH

    @pytest.mark.asyncio
    async def test_back_to_notifications_view(self):
        """Back to NOTIFICATIONS should push NotificationsScreen."""
        clear_errors()
        state = AppState()
        state.history.append(
            HistoryEntry(
                view=View.NOTIFICATIONS, target=None, scroll_position=0
            )
        )
        app = MockApp(state=state)
        async with app.run_test() as pilot:
            await app.push_screen(ErrorsScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ErrorsScreen)

            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            from freefood.screens.notifications import NotificationsScreen

            assert any(
                isinstance(s, NotificationsScreen) for s in app.pushed_screens
            )
            assert state.current_view == View.NOTIFICATIONS

    @pytest.mark.asyncio
    async def test_back_to_errors_view_refreshes(self):
        """Back to ERRORS view should call action_refresh."""
        clear_errors()

        state = AppState()
        state.history.append(
            HistoryEntry(view=View.ERRORS, target=None, scroll_position=0)
        )
        app = MockApp(state=state)
        async with app.run_test() as pilot:
            await app.push_screen(ErrorsScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ErrorsScreen)

            # Verify the back handler calls action_refresh for ERRORS view
            with patch.object(screen, "action_refresh") as mock_refresh:
                screen.on_menu_bar_back_requested(MenuBar.BackRequested())
                await pilot.pause()

                mock_refresh.assert_called_once()

            # State should be updated to ERRORS
            assert state.current_view == View.ERRORS

    @pytest.mark.asyncio
    async def test_back_to_directs_view(self):
        """Back to DIRECTS (a feed-type view) should push FeedScreen."""
        clear_errors()
        state = AppState()
        state.history.append(
            HistoryEntry(view=View.DIRECTS, target=None, scroll_position=0)
        )
        app = MockApp(state=state)
        async with app.run_test() as pilot:
            await app.push_screen(ErrorsScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ErrorsScreen)

            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)
            assert state.current_view == View.DIRECTS
