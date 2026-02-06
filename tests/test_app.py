"""Tests for FreeFoodApp."""

from unittest.mock import AsyncMock, patch

import pytest

from freefood.app import FreeFoodApp
from freefood.models import Attachment, User, View
from freefood.screens.auth import AuthScreen
from freefood.widgets.menu import MenuBar
from freefood.widgets.post import PostBlock


def test_app_importable():
    """Test that the app class can be imported and instantiated."""
    app = FreeFoodApp()
    assert app.TITLE == "FreeFood"


def test_app_init_defaults():
    """Test initial state of the app."""
    app = FreeFoodApp()
    assert app.api is None
    assert app.state is not None
    assert app.attachments is not None
    assert app.attachments.token == ""


class TestAppMount:
    """Tests for on_mount behavior."""

    @pytest.mark.asyncio
    async def test_mount_with_token_calls_try_connect(self):
        """When a token is stored, on_mount calls _try_connect."""
        mock_user = User(id="u1", username="alice", screen_name="Alice", type="user")
        mock_api = AsyncMock()
        mock_api.validate_token = AsyncMock(return_value=mock_user)
        mock_api.close = AsyncMock()

        with (
            patch("freefood.app.get_token", return_value="test-token"),
            patch("freefood.app.get_base_url", return_value="https://freefeed.net"),
            patch("freefood.app.FreeFeedAPI", return_value=mock_api),
            patch("freefood.app.save_token") as mock_save,
        ):
            async with FreeFoodApp().run_test() as pilot:
                # Token was validated and saved
                mock_api.validate_token.assert_awaited_once()
                mock_save.assert_called_once_with("test-token", "alice")
                # API was set
                assert pilot.app.api is mock_api
                # Attachment token updated
                assert pilot.app.attachments.token == "test-token"

    @pytest.mark.asyncio
    async def test_mount_without_token_shows_auth_screen(self):
        """When no token is stored, on_mount pushes AuthScreen."""
        with patch("freefood.app.get_token", return_value=None):
            async with FreeFoodApp().run_test() as pilot:
                assert isinstance(pilot.app.screen, AuthScreen)

    @pytest.mark.asyncio
    async def test_mount_with_token_connect_failure_shows_auth(self):
        """When _try_connect fails, AuthScreen is shown with error."""
        mock_api = AsyncMock()
        mock_api.validate_token = AsyncMock(side_effect=Exception("Connection refused"))
        mock_api.close = AsyncMock()

        with (
            patch("freefood.app.get_token", return_value="bad-token"),
            patch("freefood.app.get_base_url", return_value="https://freefeed.net"),
            patch("freefood.app.FreeFeedAPI", return_value=mock_api),
        ):
            async with FreeFoodApp().run_test() as pilot:
                assert isinstance(pilot.app.screen, AuthScreen)
                assert pilot.app.screen.initial_error is not None
                assert "Connection failed" in pilot.app.screen.initial_error
                # API should be cleared on failure
                assert pilot.app.api is None


class TestAuthTokenSubmitted:
    """Tests for on_auth_screen_token_submitted."""

    @pytest.mark.asyncio
    async def test_token_submitted_calls_try_connect(self):
        """Token submission pops screen and tries to connect."""
        mock_user = User(id="u1", username="bob", screen_name="Bob", type="user")
        mock_api = AsyncMock()
        mock_api.validate_token = AsyncMock(return_value=mock_user)
        mock_api.close = AsyncMock()

        with (
            patch("freefood.app.get_token", return_value=None),
            patch("freefood.app.get_base_url", return_value="https://freefeed.net"),
            patch("freefood.app.FreeFeedAPI", return_value=mock_api),
            patch("freefood.app.save_token"),
        ):
            async with FreeFoodApp().run_test() as pilot:
                # Should be on AuthScreen initially
                assert isinstance(pilot.app.screen, AuthScreen)

                # Simulate the TokenSubmitted message
                pilot.app.post_message(AuthScreen.TokenSubmitted("new-token"))
                await pilot.pause()
                await pilot.pause()

                # After successful connect, should be on FeedScreen
                mock_api.validate_token.assert_awaited()


class TestAppUnmount:
    """Tests for on_unmount cleanup."""

    @pytest.mark.asyncio
    async def test_unmount_with_api_closes_it(self):
        """on_unmount closes both API and attachments."""
        mock_user = User(id="u1", username="alice", screen_name="Alice", type="user")
        mock_api = AsyncMock()
        mock_api.validate_token = AsyncMock(return_value=mock_user)
        mock_api.close = AsyncMock()

        with (
            patch("freefood.app.get_token", return_value="test-token"),
            patch("freefood.app.get_base_url", return_value="https://freefeed.net"),
            patch("freefood.app.FreeFeedAPI", return_value=mock_api),
            patch("freefood.app.save_token"),
        ):
            async with FreeFoodApp().run_test() as pilot:
                assert pilot.app.api is not None

            # After exiting run_test, on_unmount should have been called
            mock_api.close.assert_awaited()

    @pytest.mark.asyncio
    async def test_unmount_without_api_only_closes_attachments(self):
        """on_unmount only closes attachments when there is no API."""
        with patch("freefood.app.get_token", return_value=None):
            async with FreeFoodApp().run_test() as pilot:
                assert pilot.app.api is None
                attachments_close = AsyncMock()
                pilot.app.attachments.close = attachments_close

            # Attachments close is called even without api
            attachments_close.assert_awaited()


class TestAttachmentOpened:
    """Tests for on_post_block_attachment_opened."""

    @pytest.mark.asyncio
    async def test_attachment_opened_browser_mode(self):
        """Browser mode opens URL in browser."""
        mock_user = User(id="u1", username="alice", screen_name="Alice", type="user")
        mock_api = AsyncMock()
        mock_api.validate_token = AsyncMock(return_value=mock_user)
        mock_api.close = AsyncMock()

        attachment = Attachment(
            id="a1",
            file_name="photo.jpg",
            file_size=1024,
            media_type="image/jpeg",
            url="https://example.com/photo.jpg",
        )

        with (
            patch("freefood.app.get_token", return_value="test-token"),
            patch("freefood.app.get_base_url", return_value="https://freefeed.net"),
            patch("freefood.app.FreeFeedAPI", return_value=mock_api),
            patch("freefood.app.save_token"),
            patch("freefood.config.get_attachment_open_mode", return_value="browser"),
        ):
            async with FreeFoodApp().run_test() as pilot:
                with patch.object(pilot.app.attachments, "open_browser") as mock_open:
                    msg = PostBlock.AttachmentOpened(attachment)
                    await pilot.app.on_post_block_attachment_opened(msg)
                    mock_open.assert_called_once_with("https://example.com/photo.jpg")

    @pytest.mark.asyncio
    async def test_attachment_opened_native_mode_success(self):
        """Native mode downloads and opens file."""
        mock_user = User(id="u1", username="alice", screen_name="Alice", type="user")
        mock_api = AsyncMock()
        mock_api.validate_token = AsyncMock(return_value=mock_user)
        mock_api.close = AsyncMock()

        attachment = Attachment(
            id="a1",
            file_name="photo.jpg",
            file_size=1024,
            media_type="image/jpeg",
            url="https://example.com/photo.jpg",
        )

        from pathlib import Path

        fake_path = Path("/tmp/fake/photo.jpg")

        with (
            patch("freefood.app.get_token", return_value="test-token"),
            patch("freefood.app.get_base_url", return_value="https://freefeed.net"),
            patch("freefood.app.FreeFeedAPI", return_value=mock_api),
            patch("freefood.app.save_token"),
            patch("freefood.config.get_attachment_open_mode", return_value="native"),
        ):
            async with FreeFoodApp().run_test() as pilot:
                with (
                    patch.object(
                        pilot.app.attachments,
                        "download",
                        new_callable=AsyncMock,
                        return_value=fake_path,
                    ) as mock_dl,
                    patch.object(pilot.app.attachments, "open_native") as mock_open,
                ):
                    msg = PostBlock.AttachmentOpened(attachment)
                    await pilot.app.on_post_block_attachment_opened(msg)
                    mock_dl.assert_awaited_once_with(attachment)
                    mock_open.assert_called_once_with(fake_path)

    @pytest.mark.asyncio
    async def test_attachment_opened_native_mode_download_error(self):
        """Native mode handles download failure gracefully."""
        mock_user = User(id="u1", username="alice", screen_name="Alice", type="user")
        mock_api = AsyncMock()
        mock_api.validate_token = AsyncMock(return_value=mock_user)
        mock_api.close = AsyncMock()

        attachment = Attachment(
            id="a1",
            file_name="photo.jpg",
            file_size=1024,
            media_type="image/jpeg",
            url="https://example.com/photo.jpg",
        )

        with (
            patch("freefood.app.get_token", return_value="test-token"),
            patch("freefood.app.get_base_url", return_value="https://freefeed.net"),
            patch("freefood.app.FreeFeedAPI", return_value=mock_api),
            patch("freefood.app.save_token"),
            patch("freefood.config.get_attachment_open_mode", return_value="native"),
            patch("freefood.app.log_error") as mock_log,
        ):
            async with FreeFoodApp().run_test() as pilot:
                with patch.object(
                    pilot.app.attachments,
                    "download",
                    new_callable=AsyncMock,
                    side_effect=Exception("Network error"),
                ):
                    msg = PostBlock.AttachmentOpened(attachment)
                    await pilot.app.on_post_block_attachment_opened(msg)
                    mock_log.assert_called_once()
                    assert "Failed to download" in mock_log.call_args[0][0]


class TestMenuBarViewSelected:
    """Tests for on_menu_bar_view_selected."""

    @pytest.mark.asyncio
    async def test_errors_view_selected(self):
        """Selecting ERRORS view navigates to ErrorsScreen."""
        mock_user = User(id="u1", username="alice", screen_name="Alice", type="user")
        mock_api = AsyncMock()
        mock_api.validate_token = AsyncMock(return_value=mock_user)
        mock_api.close = AsyncMock()

        with (
            patch("freefood.app.get_token", return_value="test-token"),
            patch("freefood.app.get_base_url", return_value="https://freefeed.net"),
            patch("freefood.app.FreeFeedAPI", return_value=mock_api),
            patch("freefood.app.save_token"),
        ):
            async with FreeFoodApp().run_test() as pilot:
                msg = MenuBar.ViewSelected(View.ERRORS)
                pilot.app.on_menu_bar_view_selected(msg)
                await pilot.pause()

                assert pilot.app.state.current_view == View.ERRORS
