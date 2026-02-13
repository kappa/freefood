"""Screen for displaying persistent error logs."""

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.widgets import Static

from freefood.logging import clear_errors, get_errors
from freefood.models import View
from freefood.screens.base import BaseScreen
from freefood.widgets.menu import MenuBar


class ErrorsScreen(BaseScreen):
    """Screen for displaying buffered errors."""

    BINDINGS = [
        ("escape", "focus_menu", "Menu"),
        ("f5", "refresh", "Refresh"),
        ("c", "clear_errors", "Clear Errors"),
    ]

    CSS = """
    ErrorsScreen {
        layout: vertical;
    }

    #errors-container {
        height: 1fr;
        padding: 0 1;
    }

    .error-entry {
        border: solid $error;
        margin: 1 0;
        padding: 1;
        height: auto;
    }

    .error-timestamp {
        color: $text-muted;
        margin-bottom: 1;
    }

    .error-message {
        color: $error;
        text-style: bold;
    }

    .error-exception {
        color: $text;
        margin-top: 1;
    }

    #errors-empty {
        text-align: center;
        margin-top: 5;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        yield MenuBar(View.ERRORS)
        with ScrollableContainer(id="errors-container"):
            yield from self._render_errors()

    def on_mount(self) -> None:
        """Update menu selection on mount."""
        menu = self.query_one(MenuBar)
        menu.set_view(View.ERRORS)

    def _render_errors(self):
        errors = get_errors()
        if not errors:
            yield Static("No errors logged", id="errors-empty")
            return

        for err in reversed(errors):
            with Vertical(classes="error-entry"):
                yield Static(
                    err["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    classes="error-timestamp",
                )
                yield Static(err["message"], classes="error-message")
                if err["exception"]:
                    yield Static(
                        f"Exception: {err['exception']}", classes="error-exception"
                    )

    def action_focus_menu(self) -> None:
        menu = self.query_one(MenuBar)
        menu.focus_current_view_button()

    def action_refresh(self) -> None:
        container = self.query_one("#errors-container")
        container.remove_children()
        container.mount_all(list(self._render_errors()))

    def action_clear_errors(self) -> None:
        clear_errors()
        self.action_refresh()

    def on_menu_bar_view_selected(self, message: MenuBar.ViewSelected) -> None:
        message.stop()
        if message.view == View.ERRORS:
            return

        self.app.state.navigate_to(message.view)

        if message.view == View.SEARCH:
            from freefood.screens.search import SearchScreen

            self.app.push_screen(SearchScreen(self.app.state))
        elif message.view == View.THEME:
            from freefood.screens.theme import ThemeScreen

            self.app.push_screen(ThemeScreen())
        elif message.view == View.NOTIFICATIONS:
            from freefood.screens.notifications import NotificationsScreen

            self.app.push_screen(NotificationsScreen(self.app.state))
        else:
            from freefood.screens.feed import FeedScreen

            self.app.push_screen(FeedScreen(self.app.state))

    def on_menu_bar_back_requested(self, message: MenuBar.BackRequested) -> None:
        message.stop()
        entry = self.app.state.pop_history()
        if entry:
            self.app.state.current_view = entry.view
            self.app.state.current_target = entry.target

            if entry.view == View.SEARCH:
                from freefood.screens.search import SearchScreen

                self.app.push_screen(SearchScreen(self.app.state))
            elif entry.view == View.NOTIFICATIONS:
                from freefood.screens.notifications import NotificationsScreen

                self.app.push_screen(NotificationsScreen(self.app.state))
            elif entry.view == View.ERRORS:
                # Should not really happen from history but handle anyway
                self.action_refresh()
            else:
                from freefood.screens.feed import FeedScreen

                self.app.push_screen(FeedScreen(self.app.state))
        else:
            self.notify("No history")
