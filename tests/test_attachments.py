"""Tests for attachment support."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

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

            assert "📷" in str(btn1.label)
            assert "image.jpg" in str(btn1.label)
            assert "📄" in str(btn2.label)
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
            ("image/png", "📷"),
            ("video/mp4", "🎬"),
            ("audio/mpeg", "🎵"),
            ("text/plain", "📄"),
            ("application/pdf", "📄"),
            ("application/zip", "📎"),
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

    def test_open_native_linux(self, manager):
        import subprocess

        with patch("sys.platform", "linux"), patch("subprocess.Popen") as mock_popen:
            manager.open_native(Path("/tmp/test.jpg"))
            mock_popen.assert_called_once_with(
                ["xdg-open", "/tmp/test.jpg"],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )

    def test_open_browser(self, manager):
        with patch("webbrowser.open") as mock_open:
            manager.open_browser("https://example.com")
            mock_open.assert_called_once_with("https://example.com")
