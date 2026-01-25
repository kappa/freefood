"""Main Textual application for FreeFood."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer

from freefood.api import FreeFeedAPI
from freefood.config import get_token, save_token
from freefood.screens.auth import AuthScreen
from freefood.screens.feed import FeedScreen
from freefood.state import AppState


class FreeFoodApp(App):
    """FreeFeed console client."""

    TITLE = "FreeFood"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        """Initialize app."""
        super().__init__()
        self.api: FreeFeedAPI | None = None
        self.state = AppState()

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize app on startup."""
        token = get_token()
        if token:
            await self._try_connect(token)
        else:
            self.push_screen(AuthScreen())

    async def _try_connect(self, token: str) -> None:
        """Try to connect with token."""
        self.api = FreeFeedAPI(token)
        try:
            user = await self.api.validate_token()
            save_token(token, user.username)
            self.push_screen(FeedScreen())
            self.notify(f"Welcome, {user.screen_name}!")
        except Exception as e:
            self.api = None
            self.notify(f"Connection failed: {e}", severity="error")
            self.push_screen(AuthScreen())

    async def on_auth_screen_token_submitted(
        self, message: AuthScreen.TokenSubmitted
    ) -> None:
        """Handle token submission from auth screen."""
        self.pop_screen()
        await self._try_connect(message.token)
