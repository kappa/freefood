"""Tests for MenuBar widget."""

import pytest

from freefood.widgets.menu import MenuBar


@pytest.mark.asyncio
async def test_menu_bar_updates_notifications_count():
    """MenuBar should update notifications label with count."""
    from textual.app import App
    from textual.widgets import Button

    class TestApp(App):
        def compose(self):
            yield MenuBar()

    async with TestApp().run_test() as pilot:
        app = pilot.app
        bar = app.query_one(MenuBar)
        bar.set_notifications_count(3)
        button = bar.query_one("#notifications-button", Button)
        assert button.label.plain == "Notifications (3)"


@pytest.mark.asyncio
async def test_menu_bar_updates_directs_count():
    """MenuBar should update directs label with count."""
    from textual.app import App
    from textual.widgets import Button

    class TestApp(App):
        def compose(self):
            yield MenuBar()

    async with TestApp().run_test() as pilot:
        app = pilot.app
        bar = app.query_one(MenuBar)
        bar.set_directs_count(2)
        button = bar.query_one("#directs-button", Button)
        assert button.label.plain == "Directs (2)"


@pytest.mark.asyncio
async def test_menu_bar_has_errors_button():
    """MenuBar should have an Errors button."""
    from textual.app import App
    from textual.widgets import Button

    class TestApp(App):
        def compose(self):
            yield MenuBar()

    async with TestApp().run_test() as pilot:
        button = pilot.app.query_one("#errors-button", Button)
        assert button.label.plain == "Errors"
