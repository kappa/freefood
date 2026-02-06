"""Authentication screen for first-run setup."""

import webbrowser

from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.message import Message
from textual.widgets import Button, Input, Static

from freefood.config import get_auth_url
from freefood.screens.base import BaseScreen


class AuthScreen(BaseScreen):
    """Screen for authenticating with FreeFeed."""

    CSS = """
    AuthScreen {
        align: center middle;
    }

    #auth-container {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 1 2;
    }

    #auth-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #auth-instructions {
        margin-bottom: 1;
    }

    #token-input {
        margin: 1 0;
    }

    Button {
        margin: 0 1;
    }

    #error-banner {
        background: $error;
        color: $text;
        padding: 0 1;
        margin-bottom: 1;
        display: none;
    }

    #error-banner.visible {
        display: block;
    }
    """

    def __init__(self, initial_error: str | None = None) -> None:
        """Initialize auth screen."""
        super().__init__()
        self.initial_error = initial_error

    def compose(self) -> ComposeResult:
        """Create auth screen widgets."""
        with Center():
            with Vertical(id="auth-container"):
                yield Static("Welcome to FreeFood!", id="auth-title")
                yield Static("", id="error-banner")
                yield Static(
                    "To connect your FreeFeed account:\n"
                    "1. Click 'Open Browser' to create an app token\n"
                    "2. Copy the token from FreeFeed\n"
                    "3. Paste it below and click 'Connect'",
                    id="auth-instructions",
                )
                yield Button("Open Browser", id="open-browser", variant="primary")
                yield Input(
                    placeholder="Paste your token here...",
                    id="token-input",
                    password=True,
                )
                yield Button("Connect", id="connect", variant="success")

    def on_mount(self) -> None:
        """Show initial error if provided."""
        if self.initial_error:
            self.show_error(self.initial_error)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "open-browser":
            webbrowser.open(get_auth_url())
            self.notify("Browser opened. Copy your token and paste it below.")
        elif event.button.id == "connect":
            self._attempt_connect()

    def _attempt_connect(self) -> None:
        """Try to connect with the entered token."""
        token_input = self.query_one("#token-input", Input)
        token = token_input.value.strip()

        if not token:
            self.show_error("Please enter a token")
            return

        # Store token and signal app to validate
        self.app.post_message(AuthScreen.TokenSubmitted(token))

    class TokenSubmitted(Message):
        """Message sent when user submits a token."""

        def __init__(self, token: str) -> None:
            super().__init__()
            self.token = token
