"""Smoke tests for FreeFoodApp."""

from freefood.app import FreeFoodApp


def test_app_importable():
    """Test that the app class can be imported and instantiated."""
    app = FreeFoodApp()
    assert app.TITLE == "FreeFood"
