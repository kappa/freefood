"""Base screen class with common error handling."""

from textual.screen import Screen
from textual.widgets import Static

from freefood.logging import log_error


class BaseScreen(Screen):
    """Base screen with error banner support."""

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
