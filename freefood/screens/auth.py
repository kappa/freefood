"""Authentication screen for first-run setup."""

import webbrowser

from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from freefood.config import AUTH_URL


class AuthScreen(Screen):
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

    #auth-buttons {
        align: center middle;
        height: 3;
    }

    Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Create auth screen widgets."""
        with Center():
            with Vertical(id="auth-container"):
                yield Static("Welcome to FreeFood!", id="auth-title")
                yield Static(
                    "To connect your FreeFeed account:\n"
                    "1. Click 'Open Browser' to create an app token\n"
                    "2. Copy the token from FreeFeed\n"
                    "3. Paste it below and click 'Connect'",
                    id="auth-instructions",
                )
                yield Button("Open Browser", id="open-browser", variant="primary")
                yield Input(placeholder="Paste your token here...", id="token-input", password=True)
                yield Button("Connect", id="connect", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "open-browser":
            webbrowser.open(AUTH_URL)
            self.notify("Browser opened. Copy your token and paste it below.")
        elif event.button.id == "connect":
            self._attempt_connect()

    def _attempt_connect(self) -> None:
        """Try to connect with the entered token."""
        token_input = self.query_one("#token-input", Input)
        token = token_input.value.strip()

        if not token:
            self.notify("Please enter a token", severity="error")
            return

        # Store token and signal app to validate
        self.app.post_message(AuthScreen.TokenSubmitted(token))

    class TokenSubmitted(Message):
        """Message sent when user submits a token."""

        def __init__(self, token: str) -> None:
            super().__init__()
            self.token = token
