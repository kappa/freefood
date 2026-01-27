"""Logging utilities for FreeFood."""

import logging
from datetime import datetime
from pathlib import Path

from platformdirs import user_log_dir

APP_NAME = "freefood"

_logger: logging.Logger | None = None


def get_log_path() -> Path:
    """Get platform-appropriate log file path."""
    log_dir = Path(user_log_dir(APP_NAME))
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "freefood.log"


def get_logger() -> logging.Logger:
    """Get or create the application logger."""
    global _logger
    if _logger is None:
        _logger = logging.getLogger(APP_NAME)
        _logger.setLevel(logging.DEBUG)

        # File handler
        log_path = get_log_path()
        handler = logging.FileHandler(log_path)
        handler.setLevel(logging.DEBUG)

        # Format with timestamp
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        _logger.addHandler(handler)

    return _logger


def log_error(message: str, exception: Exception | None = None) -> None:
    """Log an error message."""
    logger = get_logger()
    if exception:
        logger.error(f"{message}: {exception}", exc_info=True)
    else:
        logger.error(message)


def log_info(message: str) -> None:
    """Log an info message."""
    logger = get_logger()
    logger.info(message)
