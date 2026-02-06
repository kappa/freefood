"""Tests for AuthScreen."""

from unittest.mock import patch

import pytest
from textual.app import App
from textual.widgets import Button, Input, Static

from freefood.screens.auth import AuthScreen
from freefood.state import AppState


class MockApp(App):
    """Test app for AuthScreen tests."""

    def __init__(self) -> None:
        super().__init__()
        self.state = AppState()
        self.received_tokens: list[str] = []

    def on_auth_screen_token_submitted(
        self, message: AuthScreen.TokenSubmitted
    ) -> None:
        """Capture token submissions."""
        self.received_tokens.append(message.token)


class TestAuthScreenCompose:
    """Tests for AuthScreen widget composition."""

    @pytest.mark.asyncio
    async def test_compose_renders_all_widgets(self):
        """AuthScreen should render title, instructions, input, and buttons."""
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(AuthScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, AuthScreen)

            # Check for title
            title = screen.query_one("#auth-title", Static)
            assert "Welcome" in str(title.render())

            # Check for instructions
            instructions = screen.query_one("#auth-instructions", Static)
            assert instructions is not None

            # Check for error banner
            banner = screen.query_one("#error-banner", Static)
            assert banner is not None

            # Check for buttons
            open_browser_btn = screen.query_one("#open-browser", Button)
            assert open_browser_btn is not None

            connect_btn = screen.query_one("#connect", Button)
            assert connect_btn is not None

            # Check for token input
            token_input = screen.query_one("#token-input", Input)
            assert token_input is not None
            assert token_input.password is True


class TestAuthScreenInit:
    """Tests for AuthScreen initialization."""

    @pytest.mark.asyncio
    async def test_init_without_initial_error(self):
        """AuthScreen without initial_error should not show error."""
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(AuthScreen())
            await pilot.pause()

            banner = app.screen.query_one("#error-banner", Static)
            assert not banner.has_class("visible")

    @pytest.mark.asyncio
    async def test_init_with_initial_error(self):
        """AuthScreen with initial_error should show error on mount."""
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(AuthScreen(initial_error="Token expired"))
            await pilot.pause()

            banner = app.screen.query_one("#error-banner", Static)
            assert banner.has_class("visible")
            assert "Token expired" in str(banner.render())


class TestAuthScreenButtons:
    """Tests for AuthScreen button interactions."""

    @pytest.mark.asyncio
    async def test_open_browser_button(self):
        """Pressing 'Open Browser' should call webbrowser.open."""
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(AuthScreen())
            await pilot.pause()

            with patch("freefood.screens.auth.webbrowser.open") as mock_open:
                btn = app.screen.query_one("#open-browser", Button)
                btn.press()
                await pilot.pause()

                mock_open.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_with_empty_token_shows_error(self):
        """Pressing 'Connect' with empty input should show error."""
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(AuthScreen())
            await pilot.pause()

            # Don't enter any token, just press connect
            connect_btn = app.screen.query_one("#connect", Button)
            connect_btn.press()
            await pilot.pause()

            banner = app.screen.query_one("#error-banner", Static)
            assert banner.has_class("visible")
            assert "token" in str(banner.render()).lower()

    @pytest.mark.asyncio
    async def test_connect_with_valid_token_posts_message(self):
        """Pressing 'Connect' with a token should post TokenSubmitted."""
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(AuthScreen())
            await pilot.pause()

            # Enter a token
            token_input = app.screen.query_one("#token-input", Input)
            token_input.value = "my-secret-token"

            # Press connect
            connect_btn = app.screen.query_one("#connect", Button)
            connect_btn.press()
            await pilot.pause()

            assert app.received_tokens == ["my-secret-token"]

    @pytest.mark.asyncio
    async def test_connect_with_whitespace_only_token_shows_error(self):
        """Pressing 'Connect' with whitespace-only input should show error."""
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(AuthScreen())
            await pilot.pause()

            # Enter only whitespace
            token_input = app.screen.query_one("#token-input", Input)
            token_input.value = "   "

            # Press connect
            connect_btn = app.screen.query_one("#connect", Button)
            connect_btn.press()
            await pilot.pause()

            banner = app.screen.query_one("#error-banner", Static)
            assert banner.has_class("visible")


class TestTokenSubmittedMessage:
    """Tests for the TokenSubmitted message class."""

    def test_token_submitted_stores_token(self):
        """TokenSubmitted message should store the provided token."""
        msg = AuthScreen.TokenSubmitted("test-token-123")
        assert msg.token == "test-token-123"
