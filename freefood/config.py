"""Configuration file handling for FreeFood."""

import configparser
from pathlib import Path

from platformdirs import user_config_dir

APP_NAME = "freefood"

AUTH_SCOPES = (
    "?title=FreeFood%20(Console%20Client)"
    "&scopes=read-my-info%20read-my-files%20read-feeds%20read-users-info"
    "%20read-realtime%20manage-my-files%20manage-notifications%20manage-posts"
    "%20manage-my-feeds%20manage-profile%20manage-groups%20manage-subscription-requests"
)


def get_auth_url() -> str:
    """Get auth URL using configured base_url."""
    base_url = get_base_url()
    return f"{base_url}/settings/app-tokens/create{AUTH_SCOPES}"


def get_config_path() -> Path:
    """Get platform-appropriate config file path."""
    config_dir = Path(user_config_dir(APP_NAME))
    return config_dir / "config.ini"


def load_config() -> configparser.ConfigParser:
    """Load config from file."""
    config = configparser.ConfigParser()
    config_path = get_config_path()
    if config_path.exists():
        config.read(config_path)
    return config


def save_config(config: configparser.ConfigParser) -> None:
    """Save config to file."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        config.write(f)


def get_token() -> str | None:
    """Get stored auth token."""
    config = load_config()
    return config.get("auth", "token", fallback=None)


def get_base_url() -> str:
    """Get API base URL (defaults to https://freefeed.net)."""
    config = load_config()
    return config.get("auth", "base_url", fallback="https://freefeed.net")


def get_username() -> str | None:
    """Get stored username."""
    config = load_config()
    return config.get("user", "username", fallback=None)


def get_attachment_open_mode() -> str:
    """Get attachment open mode (native or browser, defaults to native)."""
    config = load_config()
    return config.get("attachments", "open_mode", fallback="native")


def save_token(token: str, username: str) -> None:
    """Save auth token and username, preserving other settings."""
    config = load_config()
    if "auth" not in config:
        config["auth"] = {}
    if "user" not in config:
        config["user"] = {}
    config["auth"]["token"] = token
    config["user"]["username"] = username
    save_config(config)
