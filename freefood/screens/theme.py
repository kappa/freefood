"""Theme selection screen."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Button, Static

from freefood.config import get_theme
from freefood.models import View
from freefood.screens.base import BaseScreen
from freefood.themes import THEME_OPTIONS
from freefood.widgets.menu import MenuBar


class ThemeScreen(BaseScreen):
    """Screen for selecting an interface theme."""

    CSS = """
    ThemeScreen {
        layout: vertical;
    }

    #theme-container {
        height: 1fr;
        padding: 1 2;
    }

    .theme-button {
        width: 40;
        margin: 0 0 1 0;
    }

    .theme-button.selected {
        background: $secondary;
    }
    """

    class ThemeSelected(Message):
        """Message sent when user chooses a theme."""

        def __init__(self, theme: str) -> None:
            self.theme = theme
            super().__init__()

    def compose(self) -> ComposeResult:
        yield MenuBar(View.THEME)
        with Vertical(id="theme-container"):
            yield Static("Select theme", id="theme-title")
            for theme in THEME_OPTIONS:
                yield Button(
                    theme.label,
                    id=f"theme-{theme.key}",
                    classes="theme-button",
                )

    def on_mount(self) -> None:
        self.app.state.current_view = View.THEME
        self._update_selection(get_theme())

    def _update_selection(self, selected_theme: str) -> None:
        for theme in THEME_OPTIONS:
            button = self.query_one(f"#theme-{theme.key}", Button)
            if theme.key == selected_theme:
                button.add_class("selected")
                button.label = f"✓ {theme.label}"
            else:
                button.remove_class("selected")
                button.label = theme.label

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if not button_id.startswith("theme-"):
            return

        selected_theme = button_id.removeprefix("theme-")
        self._update_selection(selected_theme)
        self.post_message(self.ThemeSelected(selected_theme))

    def on_menu_bar_view_selected(self, message: MenuBar.ViewSelected) -> None:
        message.stop()
        if message.view == View.THEME:
            return

        self.app.state.navigate_to(message.view)

        if message.view == View.SEARCH:
            from freefood.screens.search import SearchScreen

            self.app.push_screen(SearchScreen(self.app.state))
        elif message.view == View.NOTIFICATIONS:
            from freefood.screens.notifications import NotificationsScreen

            self.app.push_screen(NotificationsScreen(self.app.state))
        elif message.view == View.ERRORS:
            from freefood.screens.errors import ErrorsScreen

            self.app.push_screen(ErrorsScreen())
        else:
            from freefood.screens.feed import FeedScreen

            self.app.push_screen(FeedScreen(self.app.state))

    def on_menu_bar_back_requested(self, message: MenuBar.BackRequested) -> None:
        message.stop()
        entry = self.app.state.pop_history()
        if not entry:
            self.notify("No history")
            return

        self.app.state.current_view = entry.view
        self.app.state.current_target = entry.target
        if entry.query is not None:
            self.app.state.search_query = entry.query

        if entry.view == View.SEARCH:
            from freefood.screens.search import SearchScreen

            self.app.push_screen(SearchScreen(self.app.state))
        elif entry.view == View.NOTIFICATIONS:
            from freefood.screens.notifications import NotificationsScreen

            self.app.push_screen(NotificationsScreen(self.app.state))
        elif entry.view == View.ERRORS:
            from freefood.screens.errors import ErrorsScreen

            self.app.push_screen(ErrorsScreen())
        else:
            from freefood.screens.feed import FeedScreen

            self.app.push_screen(FeedScreen(self.app.state))
