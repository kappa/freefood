"""Attachment handling for FreeFood."""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import httpx

from freefood.logging import log_info

from .models import Attachment


class AttachmentManager:
    """Manages downloading and opening of attachments."""

    def __init__(self, session_id: str, token: str) -> None:
        """Initialize with a session ID for temp directory isolation."""
        self.session_id = session_id
        self.temp_dir = Path(tempfile.gettempdir()) / f"freefood-{session_id}"
        self._token = token
        self._client: httpx.AsyncClient | None = None

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, new_token: str) -> None:
        if new_token != self._token:
            self._token = new_token
            # Clear the client so it's re-initialized with the new token
            self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
            self._client = httpx.AsyncClient(
                timeout=60.0, follow_redirects=True, headers=headers
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client and clean up temp directory."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        self.cleanup()

    def cleanup(self) -> None:
        """Remove temp directory."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def get_local_path(self, attachment: Attachment) -> Path:
        """Get local path for an attachment (cached in temp dir)."""
        # Use attachment ID in filename to avoid collisions between same-named files
        ext = Path(attachment.file_name).suffix
        local_name = f"{attachment.id}{ext}"
        return self.temp_dir / local_name

    async def download(self, attachment: Attachment) -> Path:
        """Download attachment to temp dir if not already there."""
        local_path = self.get_local_path(attachment)
        if local_path.exists():
            return local_path

        self.temp_dir.mkdir(parents=True, exist_ok=True)
        client = await self._get_client()

        async with client.stream("GET", attachment.url) as response:
            response.raise_for_status()  # Re-enable proper error handling

            with open(local_path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)

        log_info(f"Successfully downloaded {attachment.file_name} to {local_path}")
        return local_path

    def open_native(self, local_path: Path) -> None:
        """Open file using platform-specific native app."""
        if sys.platform == "linux":
            subprocess.Popen(
                ["xdg-open", str(local_path)],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )
        elif sys.platform == "darwin":
            subprocess.Popen(
                ["open", str(local_path)],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )
        elif sys.platform == "win32":
            os.startfile(local_path)

    def open_browser(self, url: str) -> None:
        """Open URL in default browser."""
        import webbrowser

        webbrowser.open(url)
