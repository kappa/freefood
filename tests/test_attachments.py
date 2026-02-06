"""Tests for attachment support."""

import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from textual.app import App
from textual.widgets import Button

from freefood.attachments import AttachmentManager
from freefood.models import Attachment, Post, User
from freefood.widgets.post import PostBlock


def make_user(username: str = "alice") -> User:
    return User(id="u1", username=username, screen_name=username.title(), type="user")


def make_attachment(
    id: str = "att1",
    file_name: str = "test.jpg",
    media_type: str = "image/jpeg",
    url: str = "https://example.com/test.jpg",
) -> Attachment:
    return Attachment(
        id=id,
        file_name=file_name,
        file_size=1024,
        media_type=media_type,
        url=url,
    )


def make_post(attachments: list[Attachment] | None = None) -> Post:
    now = datetime.now()
    return Post(
        id="p1",
        body="Post with attachments",
        author=make_user(),
        groups=[],
        created_at=now,
        updated_at=now,
        comments=[],
        omitted_comments=0,
        omitted_comments_offset=0,
        omitted_comment_likes=0,
        omitted_likes=0,
        likes=[],
        attachments=attachments or [],
    )


class TestAttachmentModel:
    """Tests for Attachment model."""

    def test_attachment_creation(self):
        att = make_attachment(file_name="photo.png", media_type="image/png")
        assert att.id == "att1"
        assert att.file_name == "photo.png"
        assert att.media_type == "image/png"
        assert att.url == "https://example.com/test.jpg"


class TestAttachmentRendering:
    """Tests for attachment button rendering in PostBlock."""

    @pytest.mark.asyncio
    async def test_attachment_buttons_rendered(self):
        att1 = make_attachment(id="a1", file_name="image.jpg", media_type="image/jpeg")
        att2 = make_attachment(
            id="a2", file_name="doc.pdf", media_type="application/pdf"
        )
        post = make_post(attachments=[att1, att2])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            btn1 = pilot.app.query_one("#att-a1", Button)
            btn2 = pilot.app.query_one("#att-a2", Button)

            assert "image.jpg" in str(btn1.label)
            assert "doc.pdf" in str(btn2.label)

    @pytest.mark.asyncio
    async def test_filename_truncation(self):
        long_name = "this_is_a_very_long_filename_that_should_be_truncated.jpg"
        att = make_attachment(file_name=long_name)
        post = make_post(attachments=[att])

        class TestApp(App):
            def compose(self):
                yield PostBlock(post)

        async with TestApp().run_test() as pilot:
            btn = pilot.app.query_one(f"#att-{att.id}", Button)
            label = str(btn.label)
            assert "..." in label
            assert len(label) < len(long_name)

    @pytest.mark.asyncio
    async def test_icon_selection(self):
        types = [
            ("image/png", "\U0001f4f7"),
            ("video/mp4", "\U0001f3ac"),
            ("audio/mpeg", "\U0001f3b5"),
            ("text/plain", "\U0001f4c4"),
            ("application/pdf", "\U0001f4c4"),
            ("application/zip", "\U0001f4ce"),
        ]

        for media_type, icon in types:
            att = make_attachment(media_type=media_type)
            post = make_post(attachments=[att])

            class TestApp(App):
                def compose(self, p=post):
                    yield PostBlock(p)

            async with TestApp().run_test() as pilot:
                btn = pilot.app.query_one(f"#att-{att.id}", Button)
                assert icon in str(btn.label)

    @pytest.mark.asyncio
    async def test_attachment_opened_message(self):
        att = make_attachment()
        post = make_post(attachments=[att])

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.received_attachment = None

            def compose(self):
                yield PostBlock(post)

            def on_post_block_attachment_opened(
                self, message: PostBlock.AttachmentOpened
            ):
                self.received_attachment = message.attachment

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.post_mode = True  # Make buttons focusable

            btn = pilot.app.query_one(f"#att-{att.id}", Button)
            await pilot.click(btn)

            assert pilot.app.received_attachment == att


class TestAttachmentManager:
    """Tests for AttachmentManager."""

    @pytest.fixture
    def manager(self):
        manager = AttachmentManager("test-session", token="dummy-token")
        yield manager
        manager.cleanup()

    def test_temp_dir_path(self, manager):
        assert "freefood-test-session" in str(manager.temp_dir)

    def test_get_local_path(self, manager):
        att = make_attachment(id="a1", file_name="test.jpg")
        path = manager.get_local_path(att)
        assert path.name == "a1.jpg"
        assert path.parent == manager.temp_dir

    @pytest.mark.asyncio
    async def test_download(self, manager):
        att = make_attachment(url="https://example.com/file.png")
        local_path = manager.get_local_path(att)

        # Mock httpx response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        async def mock_aiter_bytes():
            yield b"content"

        mock_response.aiter_bytes = mock_aiter_bytes

        mock_client = MagicMock()
        mock_client.stream.return_value.__aenter__.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_client):
            path = await manager.download(att)
            assert path == local_path
            assert path.exists()
            assert path.read_bytes() == b"content"

    @pytest.mark.asyncio
    async def test_download_returns_cached_file(self, manager, tmp_path):
        """download() returns immediately if local file already exists."""
        att = make_attachment(id="cached1", file_name="cached.jpg")
        local_path = manager.get_local_path(att)

        # Create the file so it's "cached"
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(b"cached-content")

        # Should return immediately without downloading
        result = await manager.download(att)
        assert result == local_path
        assert result.read_bytes() == b"cached-content"

    def test_open_native_linux(self, manager):
        with patch("sys.platform", "linux"), patch("subprocess.Popen") as mock_popen:
            manager.open_native(Path("/tmp/test.jpg"))
            mock_popen.assert_called_once_with(
                ["xdg-open", "/tmp/test.jpg"],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )

    def test_open_native_darwin(self, manager):
        """open_native uses 'open' on macOS."""
        with patch("sys.platform", "darwin"), patch(
            "subprocess.Popen"
        ) as mock_popen:
            manager.open_native(Path("/tmp/test.jpg"))
            mock_popen.assert_called_once_with(
                ["open", "/tmp/test.jpg"],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )

    def test_open_native_win32(self, manager):
        """open_native uses os.startfile on Windows."""
        with patch("sys.platform", "win32"), patch(
            "os.startfile", create=True
        ) as mock_startfile:
            manager.open_native(Path("C:\\tmp\\test.jpg"))
            mock_startfile.assert_called_once_with(Path("C:\\tmp\\test.jpg"))

    def test_open_browser(self, manager):
        with patch("webbrowser.open") as mock_open:
            manager.open_browser("https://example.com")
            mock_open.assert_called_once_with("https://example.com")

    def test_token_property_getter(self, manager):
        """token property returns the stored token."""
        assert manager.token == "dummy-token"

    def test_token_setter_different_value(self, manager):
        """Setting a different token clears the client."""
        # Simulate an existing client
        manager._client = MagicMock()

        manager.token = "new-token"
        assert manager.token == "new-token"
        assert manager._client is None  # Client should be cleared

    def test_token_setter_same_value(self, manager):
        """Setting the same token does not clear the client."""
        fake_client = MagicMock()
        manager._client = fake_client

        manager.token = "dummy-token"  # Same value
        assert manager._client is fake_client  # Client should be preserved

    @pytest.mark.asyncio
    async def test_close_with_client(self, manager):
        """close() closes the httpx client and cleans up."""
        mock_client = AsyncMock()
        manager._client = mock_client

        # Create temp dir so cleanup has something to do
        manager.temp_dir.mkdir(parents=True, exist_ok=True)
        assert manager.temp_dir.exists()

        await manager.close()

        mock_client.aclose.assert_awaited_once()
        assert manager._client is None
        assert not manager.temp_dir.exists()

    @pytest.mark.asyncio
    async def test_close_without_client(self, manager):
        """close() works when no client has been created."""
        assert manager._client is None

        # Should not raise
        await manager.close()
        assert manager._client is None

    @pytest.mark.asyncio
    async def test_get_client_creates_with_token(self, manager):
        """_get_client creates an httpx.AsyncClient with auth header."""
        client = await manager._get_client()
        assert client is not None
        assert manager._client is client

        # Calling again returns the same client
        client2 = await manager._get_client()
        assert client2 is client

        # Cleanup
        await client.aclose()

    @pytest.mark.asyncio
    async def test_get_client_creates_without_token(self):
        """_get_client creates client without auth header when no token."""
        mgr = AttachmentManager("no-token-session", token="")
        client = await mgr._get_client()
        assert client is not None
        await client.aclose()
        mgr.cleanup()
