"""Main Textual application for FreeFood."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Static, Footer


class FreeFoodApp(App):
    """FreeFeed console client."""

    TITLE = "FreeFood"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("f5", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("FreeFood - Loading...", id="content")
        yield Footer()

    def action_refresh(self) -> None:
        """Refresh current view."""
        self.notify("Refreshing...")
