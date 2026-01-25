"""Configuration file handling for FreeFood."""

import configparser
from pathlib import Path

from platformdirs import user_config_dir

APP_NAME = "freefood"

AUTH_URL = (
    "https://freefeed.net/settings/app-tokens/create"
    "?title=FreeFood%20(Console%20Client)"
    "&scopes=read-my-info%20read-my-files%20read-feeds%20read-users-info"
    "%20read-realtime%20manage-my-files%20manage-notifications%20manage-posts"
    "%20manage-my-feeds%20manage-profile%20manage-groups%20manage-subscription-requests"
)


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


def save_token(token: str, username: str) -> None:
    """Save auth token and username."""
    config = load_config()
    if "auth" not in config:
        config["auth"] = {}
    if "user" not in config:
        config["user"] = {}
    config["auth"]["token"] = token
    config["user"]["username"] = username
    save_config(config)
