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
            return  # theme screen is static, nothing to refresh
        self.app.state.navigate_to(message.view)
        self.push_screen_for_view(message.view)

    def on_menu_bar_back_requested(self, message: MenuBar.BackRequested) -> None:
        message.stop()
        if not self.navigate_back():
            self.notify("No history")
