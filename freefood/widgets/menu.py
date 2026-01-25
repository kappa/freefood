"""Menu bar widget for navigation."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button

from freefood.models import View


class MenuBar(Widget):
    """Top navigation menu bar."""

    DEFAULT_CSS = """
    MenuBar {
        dock: top;
        height: 3;
        background: $primary;
        padding: 0 1;
    }

    MenuBar Horizontal {
        height: 100%;
        align: left middle;
    }

    MenuBar Button {
        margin: 0 1 0 0;
        min-width: 14;
    }

    MenuBar Button.selected {
        background: $secondary;
    }

    MenuBar #back-button {
        min-width: 8;
    }
    """

    class ViewSelected(Message):
        """Message sent when a view is selected."""

        def __init__(self, view: View) -> None:
            self.view = view
            super().__init__()

    class BackRequested(Message):
        """Message sent when back is requested."""

        pass

    def __init__(self, current_view: View = View.HOME) -> None:
        """Initialize menu bar."""
        super().__init__()
        self.current_view = current_view

    def compose(self) -> ComposeResult:
        """Create menu buttons."""
        with Horizontal():
            yield Button("← Back", id="back-button", variant="default")
            yield Button("Home", id="home-button", variant="primary")
            yield Button("Notifications", id="notifications-button")
            yield Button("Directs", id="directs-button")
            yield Button("Search", id="search-button")

    def on_mount(self) -> None:
        """Highlight current view on mount."""
        self._update_selection()

    def _update_selection(self) -> None:
        """Update button selection state."""
        view_to_button = {
            View.HOME: "home-button",
            View.NOTIFICATIONS: "notifications-button",
            View.DIRECTS: "directs-button",
            View.SEARCH: "search-button",
        }

        for view, button_id in view_to_button.items():
            button = self.query_one(f"#{button_id}", Button)
            if view == self.current_view:
                button.add_class("selected")
            else:
                button.remove_class("selected")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_to_view = {
            "home-button": View.HOME,
            "notifications-button": View.NOTIFICATIONS,
            "directs-button": View.DIRECTS,
            "search-button": View.SEARCH,
        }

        if event.button.id == "back-button":
            self.post_message(self.BackRequested())
        elif event.button.id in button_to_view:
            view = button_to_view[event.button.id]
            if view != self.current_view:
                self.current_view = view
                self._update_selection()
                self.post_message(self.ViewSelected(view))

    def set_view(self, view: View) -> None:
        """Set current view externally."""
        self.current_view = view
        self._update_selection()
