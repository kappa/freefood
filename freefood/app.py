"""Main Textual application for FreeFood."""

import uuid

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Footer

from freefood.api import FreeFeedAPI
from freefood.attachments import AttachmentManager
from freefood.base_app import FreeFoodAppBase
from freefood.config import get_base_url, get_theme, get_token, save_theme, save_token
from freefood.logging import log_error
from freefood.models import View
from freefood.screens.auth import AuthScreen
from freefood.screens.errors import ErrorsScreen
from freefood.screens.feed import FeedScreen
from freefood.screens.theme import ThemeScreen
from freefood.state import AppState
from freefood.themes import resolve_textual_theme
from freefood.widgets.menu import MenuBar
from freefood.widgets.post import PostBlock


class FreeFoodApp(FreeFoodAppBase):
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
        # The token is not available at init time, so it will be set later.
        # This is okay because attachments are only downloaded after login.
        self.attachments = AttachmentManager(str(uuid.uuid4()), token="")

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize app on startup."""
        self.apply_theme(get_theme(), persist=False)
        token = get_token()
        if token:
            await self._try_connect(token)
        else:
            self.push_screen(AuthScreen())

    async def _try_connect(self, token: str) -> None:
        """Try to connect with token."""
        base_url = get_base_url()
        self.api = FreeFeedAPI(token, base_url)
        try:
            user = await self.api.validate_token()
            save_token(token, user.username)
            self.attachments.token = token  # Update the token in AttachmentManager
            self.push_screen(FeedScreen())
            self.notify(f"Welcome, {user.screen_name}!")
        except Exception as e:
            self.api = None
            self.push_screen(AuthScreen(initial_error=f"Connection failed: {e}"))

    async def on_auth_screen_token_submitted(
        self, message: AuthScreen.TokenSubmitted
    ) -> None:
        """Handle token submission from auth screen."""
        self.pop_screen()
        await self._try_connect(message.token)

    async def on_unmount(self) -> None:
        """Clean up on exit."""
        if self.api:
            await self.api.close()
        await self.attachments.close()

    async def on_post_block_attachment_opened(
        self, message: PostBlock.AttachmentOpened
    ) -> None:
        """Handle attachment open request."""
        from freefood.config import get_attachment_open_mode

        attachment = message.attachment
        mode = get_attachment_open_mode()

        if mode == "browser":
            self.attachments.open_browser(attachment.url)
            self.notify(f"Opening in browser: {attachment.file_name}")
        else:
            self.notify(f"Downloading {attachment.file_name}...")
            try:
                local_path = await self.attachments.download(attachment)
                self.attachments.open_native(local_path)
            except Exception as e:
                log_error(f"Failed to download attachment: {attachment.file_name}", e)
                self.notify(f"Failed to download: {e}", severity="error")

    def on_menu_bar_view_selected(self, message: MenuBar.ViewSelected) -> None:
        """Handle view selection from menu bar globally."""
        if message.view == View.ERRORS:
            self.state.navigate_to(View.ERRORS)
            self.push_screen(ErrorsScreen())
        elif message.view == View.THEME:
            self.state.navigate_to(View.THEME)
            self.push_screen(ThemeScreen())

    def apply_theme(self, theme: str, persist: bool = True) -> None:
        """Apply and optionally persist a theme by key."""
        self.theme = resolve_textual_theme(theme)
        if persist:
            save_theme(theme)

    def on_theme_screen_theme_selected(
        self, message: ThemeScreen.ThemeSelected
    ) -> None:
        """Handle theme changes from ThemeScreen."""
        self.apply_theme(message.theme)
        self.notify(f"Theme switched to {message.theme}")
