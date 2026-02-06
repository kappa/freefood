"""Logging utilities for FreeFood."""

import logging
from datetime import datetime
from pathlib import Path

from platformdirs import user_log_dir

APP_NAME = "freefood"

_logger: logging.Logger | None = None
_error_buffer: list[dict] = []
MAX_BUFFER_SIZE = 100


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
    """Log an error message and store in buffer."""
    logger = get_logger()
    timestamp = datetime.now()
    full_message = f"{message}: {exception}" if exception else message
    
    if exception:
        logger.error(f"{message}: {exception}", exc_info=True)
    else:
        logger.error(message)

    # Store in buffer for UI
    _error_buffer.append({
        "timestamp": timestamp,
        "message": message,
        "exception": str(exception) if exception else None,
        "full_message": full_message
    })
    
    # Prune old errors
    while len(_error_buffer) > MAX_BUFFER_SIZE:
        _error_buffer.pop(0)


def get_errors() -> list[dict]:
    """Get buffered errors."""
    return _error_buffer


def clear_errors() -> None:
    """Clear buffered errors."""
    _error_buffer.clear()


def log_info(message: str) -> None:
    """Log an info message."""
    logger = get_logger()
    logger.info(message)
