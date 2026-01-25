"""Tests for configuration module."""

import configparser
import tempfile
from pathlib import Path
from unittest.mock import patch

from freefood.config import get_config_path, get_token, load_config, save_config, save_token


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
        with patch("freefood.config.get_config_path", return_value=Path(tmpdir) / "config.ini"):
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
        with patch("freefood.config.get_config_path", return_value=Path(tmpdir) / "config.ini"):
            assert get_token() is None


def test_save_and_get_token():
    """Saved token should be retrievable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.ini"
        with patch("freefood.config.get_config_path", return_value=config_path):
            save_token("test-token-123", "testuser")
            assert get_token() == "test-token-123"
