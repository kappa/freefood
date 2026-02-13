"""Tests for MenuBar widget."""

import pytest
from textual.app import App
from textual.widgets import Button

from freefood.models import View
from freefood.widgets.menu import MenuBar


@pytest.mark.asyncio
async def test_menu_bar_updates_notifications_count():
    """MenuBar should update notifications label with count."""

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

    class TestApp(App):
        def compose(self):
            yield MenuBar()

    async with TestApp().run_test() as pilot:
        button = pilot.app.query_one("#errors-button", Button)
        assert button.label.plain == "Errors"


@pytest.mark.asyncio
async def test_menu_bar_has_theme_button():
    """MenuBar should have a Theme button."""

    class TestApp(App):
        def compose(self):
            yield MenuBar()

    async with TestApp().run_test() as pilot:
        button = pilot.app.query_one("#theme-button", Button)
        assert button.label.plain == "Theme"


# --- on_button_pressed tests (lines 104-119) ---


@pytest.mark.asyncio
async def test_menu_bar_back_button_emits_back_requested():
    """Pressing the back button should post BackRequested."""
    messages = []

    class TestApp(App):
        def compose(self):
            yield MenuBar()

        def on_menu_bar_back_requested(self, event):
            messages.append(event)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        back_btn = app.query_one("#back-button", Button)
        back_btn.press()
        await pilot.pause()
        assert len(messages) == 1
        assert isinstance(messages[0], MenuBar.BackRequested)


@pytest.mark.asyncio
async def test_menu_bar_clicking_view_button_emits_view_selected():
    """Clicking a view button should emit ViewSelected with the view."""
    messages = []

    class TestApp(App):
        def compose(self):
            yield MenuBar()

        def on_menu_bar_view_selected(self, event):
            messages.append(event)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        bar = app.query_one(MenuBar)
        # Current view is HOME, click NOTIFICATIONS
        notif_btn = bar.query_one("#notifications-button", Button)
        notif_btn.press()
        await pilot.pause()
        assert len(messages) == 1
        assert messages[0].view == View.NOTIFICATIONS


@pytest.mark.asyncio
async def test_menu_bar_clicking_current_view_does_not_emit():
    """Clicking the already-selected view should not emit ViewSelected."""
    messages = []

    class TestApp(App):
        def compose(self):
            yield MenuBar()  # default is HOME

        def on_menu_bar_view_selected(self, event):
            messages.append(event)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        bar = app.query_one(MenuBar)
        # Click HOME which is already current
        home_btn = bar.query_one("#home-button", Button)
        home_btn.press()
        await pilot.pause()
        assert len(messages) == 0


@pytest.mark.asyncio
async def test_menu_bar_view_selection_updates_class():
    """Selecting a new view should update the 'selected' class on buttons."""

    class TestApp(App):
        def compose(self):
            yield MenuBar()

    async with TestApp().run_test() as pilot:
        app = pilot.app
        bar = app.query_one(MenuBar)

        # Initially, home should be selected
        home_btn = bar.query_one("#home-button", Button)
        assert home_btn.has_class("selected")

        # Click search
        search_btn = bar.query_one("#search-button", Button)
        search_btn.press()
        await pilot.pause()

        # Now search should be selected, home not
        assert search_btn.has_class("selected")
        assert not home_btn.has_class("selected")


@pytest.mark.asyncio
async def test_menu_bar_clicking_directs_button():
    """Clicking Directs button should emit ViewSelected with DIRECTS."""
    messages: list = []

    class TestApp(App):
        def compose(self):
            yield MenuBar(current_view=View.HOME)

        def on_menu_bar_view_selected(self, event):
            messages.append(event)

    async with TestApp().run_test() as pilot:
        bar = pilot.app.query_one(MenuBar)
        bar.query_one("#directs-button", Button).press()
        await pilot.pause()
        assert len(messages) == 1
        assert messages[0].view == View.DIRECTS


@pytest.mark.asyncio
async def test_menu_bar_clicking_search_button():
    """Clicking Search button should emit ViewSelected with SEARCH."""
    messages: list = []

    class TestApp(App):
        def compose(self):
            yield MenuBar(current_view=View.HOME)

        def on_menu_bar_view_selected(self, event):
            messages.append(event)

    async with TestApp().run_test() as pilot:
        bar = pilot.app.query_one(MenuBar)
        bar.query_one("#search-button", Button).press()
        await pilot.pause()
        assert len(messages) == 1
        assert messages[0].view == View.SEARCH


@pytest.mark.asyncio
async def test_menu_bar_clicking_errors_view_button():
    """Clicking Errors button should emit ViewSelected with ERRORS."""
    messages: list = []

    class TestApp(App):
        def compose(self):
            yield MenuBar(current_view=View.HOME)

        def on_menu_bar_view_selected(self, event):
            messages.append(event)

    async with TestApp().run_test() as pilot:
        bar = pilot.app.query_one(MenuBar)
        bar.query_one("#errors-button", Button).press()
        await pilot.pause()
        assert len(messages) == 1
        assert messages[0].view == View.ERRORS


@pytest.mark.asyncio
async def test_menu_bar_clicking_theme_button():
    """Clicking Theme button should emit ViewSelected with THEME."""
    messages: list = []

    class TestApp(App):
        def compose(self):
            yield MenuBar(current_view=View.HOME)

        def on_menu_bar_view_selected(self, event):
            messages.append(event)

    async with TestApp().run_test() as pilot:
        bar = pilot.app.query_one(MenuBar)
        bar.query_one("#theme-button", Button).press()
        await pilot.pause()
        assert len(messages) == 1
        assert messages[0].view == View.THEME


# --- focus_current_view_button tests (lines 146-154) ---


@pytest.mark.asyncio
async def test_menu_bar_focus_current_view_button():
    """focus_current_view_button should focus the button for the current view."""

    class TestApp(App):
        def compose(self):
            yield MenuBar(current_view=View.SEARCH)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        bar = app.query_one(MenuBar)
        bar.focus_current_view_button()
        await pilot.pause()
        assert app.focused.id == "search-button"


@pytest.mark.asyncio
async def test_menu_bar_focus_current_view_button_defaults_to_home():
    """focus_current_view_button should default to home for unknown views."""

    class TestApp(App):
        def compose(self):
            yield MenuBar(current_view=View.USER_FEED)

    async with TestApp().run_test() as pilot:
        app = pilot.app
        bar = app.query_one(MenuBar)
        bar.focus_current_view_button()
        await pilot.pause()
        assert app.focused.id == "home-button"


# --- action_focus_previous tests (lines 158-163) ---


@pytest.mark.asyncio
async def test_menu_bar_focus_previous_navigates_left():
    """action_focus_previous should move focus to the previous button."""

    class TestApp(App):
        def compose(self):
            yield MenuBar()

    async with TestApp().run_test() as pilot:
        app = pilot.app
        bar = app.query_one(MenuBar)
        # Focus the notifications button (index 2 in the button list)
        notif_btn = bar.query_one("#notifications-button", Button)
        notif_btn.focus()
        await pilot.pause()
        assert app.focused.id == "notifications-button"

        # Press left to go to home button
        await pilot.press("left")
        await pilot.pause()
        assert app.focused.id == "home-button"


@pytest.mark.asyncio
async def test_menu_bar_focus_previous_at_first_stays():
    """action_focus_previous at first button should stay put."""

    class TestApp(App):
        def compose(self):
            yield MenuBar()

    async with TestApp().run_test() as pilot:
        app = pilot.app
        bar = app.query_one(MenuBar)
        # Focus the back button (first)
        back_btn = bar.query_one("#back-button", Button)
        back_btn.focus()
        await pilot.pause()
        assert app.focused.id == "back-button"

        # Press left - should stay at back
        await pilot.press("left")
        await pilot.pause()
        assert app.focused.id == "back-button"


# --- action_focus_next tests (lines 167-172) ---


@pytest.mark.asyncio
async def test_menu_bar_focus_next_navigates_right():
    """action_focus_next should move focus to the next button."""

    class TestApp(App):
        def compose(self):
            yield MenuBar()

    async with TestApp().run_test() as pilot:
        app = pilot.app
        bar = app.query_one(MenuBar)
        # Focus the home button
        home_btn = bar.query_one("#home-button", Button)
        home_btn.focus()
        await pilot.pause()
        assert app.focused.id == "home-button"

        # Press right to go to notifications button
        await pilot.press("right")
        await pilot.pause()
        assert app.focused.id == "notifications-button"


@pytest.mark.asyncio
async def test_menu_bar_focus_next_at_last_stays():
    """action_focus_next at last button should stay put."""

    class TestApp(App):
        def compose(self):
            yield MenuBar()

    async with TestApp().run_test() as pilot:
        app = pilot.app
        bar = app.query_one(MenuBar)
        # Focus the errors button (last)
        errors_btn = bar.query_one("#errors-button", Button)
        errors_btn.focus()
        await pilot.pause()
        assert app.focused.id == "errors-button"

        # Press right - should stay at errors
        await pilot.press("right")
        await pilot.pause()
        assert app.focused.id == "errors-button"


# --- _update_selection preserves notification/directs counts (lines 97-100) ---


@pytest.mark.asyncio
async def test_menu_bar_update_selection_preserves_counts():
    """_update_selection should re-apply notification/directs counts."""

    class TestApp(App):
        def compose(self):
            yield MenuBar()

    async with TestApp().run_test() as pilot:
        app = pilot.app
        bar = app.query_one(MenuBar)

        # Set counts
        bar.set_notifications_count(5)
        bar.set_directs_count(3)

        # Now change view (which triggers _update_selection internally)
        bar.set_view(View.SEARCH)
        await pilot.pause()

        # Counts should be preserved in labels
        notif_btn = bar.query_one("#notifications-button", Button)
        assert notif_btn.label.plain == "Notifications (5)"
        directs_btn = bar.query_one("#directs-button", Button)
        assert directs_btn.label.plain == "Directs (3)"


@pytest.mark.asyncio
async def test_menu_bar_zero_count_shows_plain_label():
    """Setting count to 0 should show plain label without count."""

    class TestApp(App):
        def compose(self):
            yield MenuBar()

    async with TestApp().run_test() as pilot:
        app = pilot.app
        bar = app.query_one(MenuBar)
        bar.set_notifications_count(0)
        bar.set_directs_count(0)

        notif_btn = bar.query_one("#notifications-button", Button)
        assert notif_btn.label.plain == "Notifications"
        directs_btn = bar.query_one("#directs-button", Button)
        assert directs_btn.label.plain == "Directs"


@pytest.mark.asyncio
async def test_menu_bar_action_focus_previous_no_button_focused():
    """action_focus_previous when no button is focused should do nothing."""

    class TestApp(App):
        def compose(self):
            yield MenuBar()

    async with TestApp().run_test() as pilot:
        app = pilot.app
        bar = app.query_one(MenuBar)
        # Focus the bar itself, not a button
        bar.focus()
        await pilot.pause()
        # Trigger action - should not crash
        bar.action_focus_previous()
        await pilot.pause()


@pytest.mark.asyncio
async def test_menu_bar_action_focus_next_no_button_focused():
    """action_focus_next when no button is focused should do nothing."""

    class TestApp(App):
        def compose(self):
            yield MenuBar()

    async with TestApp().run_test() as pilot:
        app = pilot.app
        bar = app.query_one(MenuBar)
        # Focus the bar itself, not a button
        bar.focus()
        await pilot.pause()
        # Trigger action - should not crash
        bar.action_focus_next()
        await pilot.pause()
