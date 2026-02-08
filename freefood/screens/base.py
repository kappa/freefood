"""Base screen class with common error handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.screen import Screen
from textual.widgets import Static

from freefood.base_app import FreeFoodAppBase
from freefood.logging import log_error

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
