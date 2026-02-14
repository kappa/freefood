"""Base screen class with common error handling and navigation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.screen import Screen
from textual.widgets import Static

from freefood.base_app import FreeFoodAppBase
from freefood.logging import log_error
from freefood.models import View

if TYPE_CHECKING:
    from freefood.api import FreeFeedAPI


class BaseScreen(Screen):
    """Base screen with error banner support."""

    @property
    def app(self) -> FreeFoodAppBase:  # type: ignore[override]
        """Return app with proper type for screens."""
        return super().app  # type: ignore[return-value]

    @property
    def api(self) -> FreeFeedAPI:
        """Return API client, asserting it's available."""
        api = self.app.api
        assert api is not None, "Not connected"
        return api

    # Subclasses should include this in their CSS
    ERROR_BANNER_CSS = """
    #error-banner {
        background: $error;
        color: $text;
        padding: 0 1;
        display: none;
    }

    #error-banner.visible {
        display: block;
    }
    """

    def show_error(self, message: str, exception: Exception | None = None) -> None:
        """Show error in banner and log it."""
        full_message = f"{message}: {exception}" if exception else message
        log_error(message, exception)
        try:
            banner = self.query_one("#error-banner", Static)
            banner.update(f"Error: {full_message}")
            banner.add_class("visible")
        except Exception:
            pass

    def hide_error(self) -> None:
        """Hide the error banner."""
        try:
            banner = self.query_one("#error-banner", Static)
            banner.remove_class("visible")
        except Exception:
            pass

    def push_screen_for_view(self, view: View) -> None:
        """Push the appropriate screen for a given view."""
        from freefood.screens.errors import ErrorsScreen
        from freefood.screens.feed import FeedScreen
        from freefood.screens.notifications import NotificationsScreen
        from freefood.screens.search import SearchScreen
        from freefood.screens.theme import ThemeScreen

        state = self.app.state
        if view == View.SEARCH:
            self.app.push_screen(SearchScreen(state))
        elif view == View.NOTIFICATIONS:
            self.app.push_screen(NotificationsScreen(state))
        elif view == View.ERRORS:
            self.app.push_screen(ErrorsScreen())
        elif view == View.THEME:
            self.app.push_screen(ThemeScreen())
        else:
            self.app.push_screen(FeedScreen(state))

    def navigate_back(self) -> bool:
        """Pop history, restore state, pop screen back to previous."""
        entry = self.app.state.pop_history()
        if not entry:
            return False
        self.app.state.current_view = entry.view
        self.app.state.current_target = entry.target
        if entry.query is not None:
            self.app.state.search_query = entry.query
        self.app.pop_screen()
        return True
