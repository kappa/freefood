"""Base application class for FreeFood to break circular dependencies."""

from collections.abc import Awaitable, Callable
from typing import Any

from textual.app import App

from freefood.state import AppState


class FreeFoodAppBase(App):
    """Base class for FreeFoodApp defining the interface for screens."""

    api: Any | None  # Typed as Any to avoid importing FreeFeedAPI here
    state: AppState

    def __init__(self) -> None:
        """Initialize the base app."""
        super().__init__()
        # These will be set by the actual implementation in app.py
        self.api = None 
        self.state = AppState()
