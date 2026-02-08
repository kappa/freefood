"""Base application class for FreeFood to break circular dependencies."""

from textual.app import App

from freefood.api import FreeFeedAPI
from freefood.state import AppState


class FreeFoodAppBase(App):
    """Base class for FreeFoodApp defining the interface for screens."""

    api: FreeFeedAPI | None
    state: AppState
