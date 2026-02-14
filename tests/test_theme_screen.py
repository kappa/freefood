"""Tests for ThemeScreen."""

from unittest.mock import patch

import pytest
from textual.app import App
from textual.widgets import Button, Static

from freefood.models import HistoryEntry, View
from freefood.screens.theme import ThemeScreen
from freefood.state import AppState
from freefood.themes import THEME_OPTIONS
from freefood.widgets.menu import MenuBar


class MockApp(App):
    def __init__(self, state: AppState | None = None) -> None:
        super().__init__()
        self.state = state or AppState()
        self.pushed_screens: list = []
        self._original_push = None

    async def on_mount(self) -> None:
        self._original_push = self.push_screen

        def tracking_push(screen, *args, **kwargs):
            self.pushed_screens.append(screen)
            return self._original_push(screen, *args, **kwargs)

        self.push_screen = tracking_push  # type: ignore[assignment]


class TestThemeScreenCompose:
    """Tests for ThemeScreen composition and mount."""

    @pytest.mark.asyncio
    async def test_theme_screen_renders_menu_bar(self):
        """ThemeScreen should render a MenuBar."""
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(ThemeScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ThemeScreen)
            assert screen.query_one(MenuBar)

    @pytest.mark.asyncio
    async def test_theme_screen_renders_title(self):
        """ThemeScreen should display 'Select theme' title."""
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(ThemeScreen())
            await pilot.pause()

            title = app.screen.query_one("#theme-title", Static)
            assert "Select theme" in str(title.render())

    @pytest.mark.asyncio
    async def test_theme_screen_renders_theme_buttons(self):
        """ThemeScreen should have a button for each theme option."""
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(ThemeScreen())
            await pilot.pause()

            for option in THEME_OPTIONS:
                button = app.screen.query_one(f"#theme-{option.key}", Button)
                assert button is not None

    @pytest.mark.asyncio
    async def test_theme_screen_sets_current_view_on_mount(self):
        """ThemeScreen should set state.current_view to THEME on mount."""
        state = AppState()
        app = MockApp(state=state)
        async with app.run_test() as pilot:
            await app.push_screen(ThemeScreen())
            await pilot.pause()

            assert state.current_view == View.THEME


class TestThemeScreenSelection:
    """Tests for theme selection behavior."""

    @pytest.mark.asyncio
    async def test_current_theme_is_marked_selected(self):
        """The current theme button should have 'selected' class and checkmark."""
        app = MockApp()
        async with app.run_test() as pilot:
            with patch("freefood.screens.theme.get_theme", return_value="dark"):
                await app.push_screen(ThemeScreen())
                await pilot.pause()

            dark_btn = app.screen.query_one("#theme-dark", Button)
            assert dark_btn.has_class("selected")
            assert "✓" in str(dark_btn.label)

    @pytest.mark.asyncio
    async def test_non_selected_theme_has_no_checkmark(self):
        """Non-selected theme buttons should not have checkmark or selected class."""
        app = MockApp()
        async with app.run_test() as pilot:
            with patch("freefood.screens.theme.get_theme", return_value="dark"):
                await app.push_screen(ThemeScreen())
                await pilot.pause()

            light_btn = app.screen.query_one("#theme-light", Button)
            assert not light_btn.has_class("selected")
            assert "✓" not in str(light_btn.label)

    @pytest.mark.asyncio
    async def test_clicking_theme_posts_theme_selected_message(self):
        """Clicking a theme button should post ThemeSelected message."""
        messages = []

        class TrackingApp(MockApp):
            def on_theme_screen_theme_selected(self, message):
                messages.append(message)

        app = TrackingApp()
        async with app.run_test() as pilot:
            with patch("freefood.screens.theme.get_theme", return_value="dark"):
                await app.push_screen(ThemeScreen())
                await pilot.pause()

            light_btn = app.screen.query_one("#theme-light", Button)
            light_btn.press()
            await pilot.pause()

            assert len(messages) == 1
            assert messages[0].theme == "light"

    @pytest.mark.asyncio
    async def test_clicking_theme_updates_selection_visuals(self):
        """Clicking a theme button should update selected class and checkmark."""
        app = MockApp()
        async with app.run_test() as pilot:
            with patch("freefood.screens.theme.get_theme", return_value="dark"):
                await app.push_screen(ThemeScreen())
                await pilot.pause()

            # Click light theme
            light_btn = app.screen.query_one("#theme-light", Button)
            light_btn.press()
            await pilot.pause()

            # Light should now be selected
            assert light_btn.has_class("selected")
            assert "✓" in str(light_btn.label)

            # Dark should no longer be selected
            dark_btn = app.screen.query_one("#theme-dark", Button)
            assert not dark_btn.has_class("selected")
            assert "✓" not in str(dark_btn.label)

    @pytest.mark.asyncio
    async def test_non_theme_button_press_ignored(self):
        """Pressing a button without theme- prefix should be ignored."""
        messages = []

        class TrackingApp(MockApp):
            def on_theme_screen_theme_selected(self, message):
                messages.append(message)

        app = TrackingApp()
        async with app.run_test() as pilot:
            with patch("freefood.screens.theme.get_theme", return_value="dark"):
                await app.push_screen(ThemeScreen())
                await pilot.pause()

            # Press back button (not a theme button)
            back_btn = app.screen.query_one("#back-button", Button)
            back_btn.press()
            await pilot.pause()

            # No ThemeSelected message should have been posted
            assert len(messages) == 0


class TestThemeScreenMenuNavigation:
    """Tests for menu bar view selection."""

    @pytest.mark.asyncio
    async def test_selecting_theme_view_is_noop(self):
        """Selecting THEME view from menu should do nothing (already there)."""
        app = MockApp()
        async with app.run_test() as pilot:
            with patch("freefood.screens.theme.get_theme", return_value="dark"):
                await app.push_screen(ThemeScreen())
                await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ThemeScreen)

            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.THEME))
            await pilot.pause()

            assert isinstance(app.screen, ThemeScreen)

    @pytest.mark.asyncio
    async def test_selecting_home_view_navigates(self):
        """Selecting HOME view should push FeedScreen."""
        app = MockApp()
        async with app.run_test() as pilot:
            with patch("freefood.screens.theme.get_theme", return_value="dark"):
                await app.push_screen(ThemeScreen())
                await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ThemeScreen)

            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.HOME))
            await pilot.pause()

            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_selecting_search_view_navigates(self):
        """Selecting SEARCH view should push SearchScreen."""
        app = MockApp()
        async with app.run_test() as pilot:
            with patch("freefood.screens.theme.get_theme", return_value="dark"):
                await app.push_screen(ThemeScreen())
                await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ThemeScreen)

            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.SEARCH))
            await pilot.pause()

            from freefood.screens.search import SearchScreen

            assert any(isinstance(s, SearchScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_selecting_notifications_view_navigates(self):
        """Selecting NOTIFICATIONS view should push NotificationsScreen."""
        app = MockApp()
        async with app.run_test() as pilot:
            with patch("freefood.screens.theme.get_theme", return_value="dark"):
                await app.push_screen(ThemeScreen())
                await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ThemeScreen)

            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.NOTIFICATIONS))
            await pilot.pause()

            from freefood.screens.notifications import NotificationsScreen

            assert any(isinstance(s, NotificationsScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_selecting_errors_view_navigates(self):
        """Selecting ERRORS view should push ErrorsScreen."""
        app = MockApp()
        async with app.run_test() as pilot:
            with patch("freefood.screens.theme.get_theme", return_value="dark"):
                await app.push_screen(ThemeScreen())
                await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ThemeScreen)

            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.ERRORS))
            await pilot.pause()

            from freefood.screens.errors import ErrorsScreen

            assert any(isinstance(s, ErrorsScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_view_selected_stops_message(self):
        """on_menu_bar_view_selected should stop the message."""
        app = MockApp()
        async with app.run_test() as pilot:
            with patch("freefood.screens.theme.get_theme", return_value="dark"):
                await app.push_screen(ThemeScreen())
                await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ThemeScreen)

            msg = MenuBar.ViewSelected(View.HOME)
            screen.on_menu_bar_view_selected(msg)
            await pilot.pause()

            assert msg._stop_propagation


class TestThemeScreenBackNavigation:
    """Tests for back navigation via menu bar."""

    @pytest.mark.asyncio
    async def test_back_with_no_history_notifies(self):
        """Back with empty history should show 'No history' notification."""
        state = AppState()
        app = MockApp(state=state)
        async with app.run_test(notifications=True) as pilot:
            with patch("freefood.screens.theme.get_theme", return_value="dark"):
                await app.push_screen(ThemeScreen())
                await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ThemeScreen)

            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            assert len(app._notifications) > 0
            assert any("No history" in str(n.message) for n in app._notifications)

    @pytest.mark.asyncio
    async def test_back_to_home_pops_screen(self):
        """Back to HOME should pop the current screen."""
        state = AppState()
        state.history.append(
            HistoryEntry(view=View.HOME, target=None, scroll_position=0)
        )
        app = MockApp(state=state)
        async with app.run_test() as pilot:
            with patch("freefood.screens.theme.get_theme", return_value="dark"):
                await app.push_screen(ThemeScreen())
                await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ThemeScreen)

            stack_size_before = len(app.screen_stack)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            assert len(app.screen_stack) < stack_size_before
            assert state.current_view == View.HOME

    @pytest.mark.asyncio
    async def test_back_to_search_pops_screen(self):
        """Back to SEARCH should pop the current screen."""
        state = AppState()
        state.history.append(
            HistoryEntry(view=View.SEARCH, target=None, scroll_position=0, query="test")
        )
        app = MockApp(state=state)
        async with app.run_test() as pilot:
            with patch("freefood.screens.theme.get_theme", return_value="dark"):
                await app.push_screen(ThemeScreen())
                await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ThemeScreen)

            stack_size_before = len(app.screen_stack)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            assert len(app.screen_stack) < stack_size_before
            assert state.current_view == View.SEARCH
            assert state.search_query == "test"

    @pytest.mark.asyncio
    async def test_back_to_notifications_pops_screen(self):
        """Back to NOTIFICATIONS should pop the current screen."""
        state = AppState()
        state.history.append(
            HistoryEntry(view=View.NOTIFICATIONS, target=None, scroll_position=0)
        )
        app = MockApp(state=state)
        async with app.run_test() as pilot:
            with patch("freefood.screens.theme.get_theme", return_value="dark"):
                await app.push_screen(ThemeScreen())
                await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ThemeScreen)

            stack_size_before = len(app.screen_stack)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            assert len(app.screen_stack) < stack_size_before
            assert state.current_view == View.NOTIFICATIONS

    @pytest.mark.asyncio
    async def test_back_stops_message(self):
        """on_menu_bar_back_requested should stop the message."""
        state = AppState()
        app = MockApp(state=state)
        async with app.run_test() as pilot:
            with patch("freefood.screens.theme.get_theme", return_value="dark"):
                await app.push_screen(ThemeScreen())
                await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ThemeScreen)

            msg = MenuBar.BackRequested()
            screen.on_menu_bar_back_requested(msg)
            await pilot.pause()

            assert msg._stop_propagation
