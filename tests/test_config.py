"""Tests for configuration module."""

import configparser
import tempfile
from pathlib import Path
from unittest.mock import patch

from freefood.config import (
    get_attachment_open_mode,
    get_auth_url,
    get_base_url,
    get_config_path,
    get_token,
    get_username,
    load_config,
    save_config,
    save_token,
)


def test_get_config_path_returns_path():
    """Config path should be a Path object."""
    path = get_config_path()
    assert isinstance(path, Path)


def test_get_config_path_ends_with_config_ini():
    """Config path should end with config.ini."""
    path = get_config_path()
    assert path.name == "config.ini"


def test_get_config_path_contains_freefood():
    """Config path should contain 'freefood' directory."""
    path = get_config_path()
    assert "freefood" in str(path)


def test_load_config_returns_configparser():
    """load_config should return a ConfigParser."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch(
            "freefood.config.get_config_path", return_value=Path(tmpdir) / "config.ini"
        ):
            config = load_config()
            assert isinstance(config, configparser.ConfigParser)


def test_save_and_load_config():
    """Saved config should be loadable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.ini"
        with patch("freefood.config.get_config_path", return_value=config_path):
            config = configparser.ConfigParser()
            config["test"] = {"key": "value"}
            save_config(config)

            loaded = load_config()
            assert loaded.get("test", "key") == "value"


def test_get_token_returns_none_when_missing():
    """get_token should return None if no token saved."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch(
            "freefood.config.get_config_path", return_value=Path(tmpdir) / "config.ini"
        ):
            assert get_token() is None


def test_save_and_get_token():
    """Saved token should be retrievable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.ini"
        with patch("freefood.config.get_config_path", return_value=config_path):
            save_token("test-token-123", "testuser")
            assert get_token() == "test-token-123"


class TestGetAttachmentOpenMode:
    """Tests for get_attachment_open_mode."""

    def test_default_is_native(self):
        """Default attachment open mode should be 'native'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"
            with patch("freefood.config.get_config_path", return_value=config_path):
                mode = get_attachment_open_mode()
                assert mode == "native"

    def test_configured_browser_mode(self):
        """Configured 'browser' mode should be returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"
            with patch("freefood.config.get_config_path", return_value=config_path):
                config = configparser.ConfigParser()
                config["attachments"] = {"open_mode": "browser"}
                save_config(config)

                mode = get_attachment_open_mode()
                assert mode == "browser"


class TestGetAuthUrl:
    """Tests for get_auth_url."""

    def test_default_auth_url(self):
        """Auth URL should use default base URL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"
            with patch("freefood.config.get_config_path", return_value=config_path):
                url = get_auth_url()
                assert url.startswith("https://freefeed.net/settings/app-tokens/create")

    def test_custom_base_url_auth(self):
        """Auth URL should use custom base URL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"
            with patch("freefood.config.get_config_path", return_value=config_path):
                config = configparser.ConfigParser()
                config["auth"] = {"base_url": "https://custom.example.com"}
                save_config(config)

                url = get_auth_url()
                assert url.startswith(
                    "https://custom.example.com/settings/app-tokens/create"
                )


class TestGetBaseUrl:
    """Tests for get_base_url."""

    def test_default_base_url(self):
        """Default base URL should be https://freefeed.net."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"
            with patch("freefood.config.get_config_path", return_value=config_path):
                url = get_base_url()
                assert url == "https://freefeed.net"


class TestGetUsername:
    """Tests for get_username."""

    def test_no_username_returns_none(self):
        """get_username returns None when not configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"
            with patch("freefood.config.get_config_path", return_value=config_path):
                assert get_username() is None

    def test_saved_username_returned(self):
        """get_username returns saved username."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"
            with patch("freefood.config.get_config_path", return_value=config_path):
                save_token("tok", "alice")
                assert get_username() == "alice"


class TestSaveTokenPreservesSettings:
    """Tests for save_token preserving existing config."""

    def test_preserves_existing_sections(self):
        """save_token should not overwrite existing non-auth sections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"
            with patch("freefood.config.get_config_path", return_value=config_path):
                # Save some config first
                config = configparser.ConfigParser()
                config["attachments"] = {"open_mode": "browser"}
                save_config(config)

                # Now save token
                save_token("my-token", "bob")

                # Verify attachments setting is preserved
                loaded = load_config()
                assert loaded.get("attachments", "open_mode") == "browser"
                assert loaded.get("auth", "token") == "my-token"
                assert loaded.get("user", "username") == "bob"

    def test_save_token_when_auth_and_user_exist(self):
        """save_token overwrites existing auth/user sections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"
            with patch("freefood.config.get_config_path", return_value=config_path):
                # Save initial token
                save_token("old-token", "old-user")
                # Overwrite
                save_token("new-token", "new-user")

                loaded = load_config()
                assert loaded.get("auth", "token") == "new-token"
                assert loaded.get("user", "username") == "new-user"
