"""Menu bar widget for navigation."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button

from freefood.models import View


class MenuBar(Widget):
    """Top navigation menu bar."""

    BINDINGS = [
        ("left", "focus_previous", "Previous"),
        ("right", "focus_next", "Next"),
    ]

    DEFAULT_CSS = """
    MenuBar {
        dock: top;
        height: auto;
        background: $primary;
    }

    MenuBar Horizontal {
        height: auto;
    }

    MenuBar > Horizontal > Button {
        border: none !important;
        height: 1;
        margin: 0 1 0 0;
        min-width: 10;
    }

    MenuBar Button.selected {
        background: $secondary;
    }

    MenuBar #back-button {
        min-width: 6;
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
        self.notifications_count: int | None = None
        self.directs_count: int | None = None

    def compose(self) -> ComposeResult:
        """Create menu buttons."""
        with Horizontal():
            yield Button("← Back", id="back-button")
            yield Button("Home", id="home-button")
            yield Button("Notifications", id="notifications-button")
            yield Button("Directs", id="directs-button")
            yield Button("Search", id="search-button")
            yield Button("Errors", id="errors-button")

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
            View.ERRORS: "errors-button",
        }

        for view, button_id in view_to_button.items():
            button = self.query_one(f"#{button_id}", Button)
            if view == self.current_view:
                button.add_class("selected")
            else:
                button.remove_class("selected")

        if self.notifications_count is not None:
            self.set_notifications_count(self.notifications_count)
        if self.directs_count is not None:
            self.set_directs_count(self.directs_count)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_to_view = {
            "home-button": View.HOME,
            "notifications-button": View.NOTIFICATIONS,
            "directs-button": View.DIRECTS,
            "search-button": View.SEARCH,
            "errors-button": View.ERRORS,
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

    def set_notifications_count(self, count: int) -> None:
        """Update notifications button label with unread count."""
        self.notifications_count = count
        label = "Notifications"
        if count > 0:
            label = f"Notifications ({count})"
        button = self.query_one("#notifications-button", Button)
        button.label = label

    def set_directs_count(self, count: int) -> None:
        """Update directs button label with unread count."""
        self.directs_count = count
        label = "Directs"
        if count > 0:
            label = f"Directs ({count})"
        button = self.query_one("#directs-button", Button)
        button.label = label

    def focus_current_view_button(self) -> None:
        """Focus the button for the current view."""
        view_to_button = {
            View.HOME: "home-button",
            View.NOTIFICATIONS: "notifications-button",
            View.DIRECTS: "directs-button",
            View.SEARCH: "search-button",
            View.ERRORS: "errors-button",
        }
        button_id = view_to_button.get(self.current_view, "home-button")
        self.query_one(f"#{button_id}", Button).focus()

    def action_focus_previous(self) -> None:
        """Focus previous button."""
        buttons = list(self.query(Button))
        focused = self.app.focused
        if isinstance(focused, Button) and focused in buttons:
            idx = buttons.index(focused)
            if idx > 0:
                buttons[idx - 1].focus()

    def action_focus_next(self) -> None:
        """Focus next button."""
        buttons = list(self.query(Button))
        focused = self.app.focused
        if isinstance(focused, Button) and focused in buttons:
            idx = buttons.index(focused)
            if idx < len(buttons) - 1:
                buttons[idx + 1].focus()
