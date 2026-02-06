"""Tests for BaseScreen error banner support."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static

from freefood.screens.base import BaseScreen


class ScreenWithBanner(BaseScreen):
    """Test screen that includes an error-banner widget."""

    CSS = BaseScreen.ERROR_BANNER_CSS

    def compose(self) -> ComposeResult:
        yield Static("", id="error-banner")
        yield Static("Main content", id="main")


class ScreenWithoutBanner(BaseScreen):
    """Test screen that does NOT include an error-banner widget."""

    def compose(self) -> ComposeResult:
        yield Static("Main content", id="main")


class TestShowError:
    """Tests for BaseScreen.show_error."""

    @pytest.mark.asyncio
    async def test_show_error_displays_message(self):
        """show_error should display the message in the error banner."""
        app = App()
        async with app.run_test() as pilot:
            screen = ScreenWithBanner()
            await app.push_screen(screen)
            await pilot.pause()

            screen.show_error("Something went wrong")
            await pilot.pause()

            banner = screen.query_one("#error-banner", Static)
            assert "Something went wrong" in str(banner.render())
            assert banner.has_class("visible")

    @pytest.mark.asyncio
    async def test_show_error_with_exception(self):
        """show_error with exception should include exception text."""
        app = App()
        async with app.run_test() as pilot:
            screen = ScreenWithBanner()
            await app.push_screen(screen)
            await pilot.pause()

            screen.show_error("Failed", Exception("timeout"))
            await pilot.pause()

            banner = screen.query_one("#error-banner", Static)
            rendered = str(banner.render())
            assert "Failed" in rendered
            assert "timeout" in rendered
            assert banner.has_class("visible")

    @pytest.mark.asyncio
    async def test_show_error_without_banner_does_not_crash(self):
        """show_error should silently pass when no error-banner exists."""
        app = App()
        async with app.run_test() as pilot:
            screen = ScreenWithoutBanner()
            await app.push_screen(screen)
            await pilot.pause()

            # Should not raise any exception
            screen.show_error("No banner here")
            await pilot.pause()


class TestHideError:
    """Tests for BaseScreen.hide_error."""

    @pytest.mark.asyncio
    async def test_hide_error_removes_visible_class(self):
        """hide_error should remove the visible class from the error banner."""
        app = App()
        async with app.run_test() as pilot:
            screen = ScreenWithBanner()
            await app.push_screen(screen)
            await pilot.pause()

            # First show an error
            screen.show_error("Visible error")
            await pilot.pause()

            banner = screen.query_one("#error-banner", Static)
            assert banner.has_class("visible")

            # Now hide it
            screen.hide_error()
            await pilot.pause()

            assert not banner.has_class("visible")

    @pytest.mark.asyncio
    async def test_hide_error_without_banner_does_not_crash(self):
        """hide_error should silently pass when no error-banner exists."""
        app = App()
        async with app.run_test() as pilot:
            screen = ScreenWithoutBanner()
            await app.push_screen(screen)
            await pilot.pause()

            # Should not raise any exception
            screen.hide_error()
            await pilot.pause()
