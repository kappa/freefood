"""Tests for NotificationsScreen behavior."""

from datetime import datetime

import pytest

from freefood.models import Notification, User, View
from freefood.screens.notifications import NotificationsScreen
from freefood.state import AppState
from freefood.widgets.notification import NotificationBlock


def make_user(username: str = "alice") -> User:
    """Create a test user."""
    return User(id="u1", username=username, screen_name=username.title(), type="user")


def make_notification(event_type: str = "post_like") -> Notification:
    """Create a test notification."""
    return Notification(
        id="n1",
        event_id="e1",
        event_type=event_type,
        date=datetime.now(),
        created_user=make_user("alice"),
        post_id="p1",
        comment_id=None,
    )


class FakeAPI:
    """Minimal API stub for notifications."""

    def __init__(self, notifications: list[Notification]) -> None:
        self.notifications = notifications
        self.calls: int = 0

    async def get_notifications(
        self, offset: int = 0, limit: int = 30
    ) -> list[Notification]:
        self.calls += 1
        return self.notifications


class TestNotificationsScreen:
    """Tests for NotificationsScreen."""

    @pytest.mark.asyncio
    async def test_empty_state_when_no_notifications(self):
        """NotificationsScreen should show empty state when list is empty."""
        from textual.app import App
        from textual.widgets import Static

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI([])
                self.state = AppState(current_view=View.NOTIFICATIONS)

            def on_mount(self) -> None:
                self.push_screen(NotificationsScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            screen.query_one("#notifications-empty", Static)

    @pytest.mark.asyncio
    async def test_loads_notifications(self):
        """NotificationsScreen should call API and render blocks."""
        from textual.app import App

        notifications = [make_notification()]
        api = FakeAPI(notifications)

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = api
                self.state = AppState(current_view=View.NOTIFICATIONS)

            def on_mount(self) -> None:
                self.push_screen(NotificationsScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert api.calls == 1
            assert screen.query(NotificationBlock).first() is not None

    @pytest.mark.asyncio
    async def test_unread_count_updates_menu(self):
        """NotificationsScreen should update menu label with unread count."""
        from textual.app import App
        from textual.widgets import Button

        notifications = [make_notification()]

        class FakeAPI:
            async def get_notifications(self, offset: int = 0, limit: int = 30):
                return notifications

            async def get_unread_notifications_count(self) -> int:
                return 4

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(current_view=View.NOTIFICATIONS)

            def on_mount(self) -> None:
                self.push_screen(NotificationsScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            menu = screen.query_one("#notifications-button", Button)
            assert menu.label.plain == "Notifications (4)"

    @pytest.mark.asyncio
    async def test_user_click_navigates_to_user_feed(self):
        """UserClicked should navigate to the user feed."""
        from textual.app import App

        notifications = [make_notification()]

        class FakeAPI:
            async def get_notifications(self, offset: int = 0, limit: int = 30):
                return notifications

            async def get_user_feed(self, username: str):
                return []

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(current_view=View.NOTIFICATIONS)

            def on_mount(self) -> None:
                self.push_screen(NotificationsScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            screen.on_notification_block_user_clicked(
                NotificationBlock.UserClicked("bob", "user")
            )
            await pilot.pause()

            assert screen.state.current_view == View.USER_FEED
            assert screen.state.current_target == "bob"

    @pytest.mark.asyncio
    async def test_post_click_opens_post_screen(self):
        """PostClicked should open PostScreen."""
        from textual.app import App

        from freefood.models import Post

        notifications = [make_notification()]

        class FakeAPI:
            async def get_notifications(self, offset: int = 0, limit: int = 30):
                return notifications

            async def get_post(self, post_id: str) -> Post:
                from tests.test_post_widget import make_post

                return make_post(id=post_id)

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI()
                self.state = AppState(current_view=View.NOTIFICATIONS)

            def on_mount(self) -> None:
                self.push_screen(NotificationsScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            await screen.on_notification_block_post_clicked(
                NotificationBlock.PostClicked("p1")
            )
            await pilot.pause()

            from freefood.screens.post import PostScreen

            assert isinstance(pilot.app.screen, PostScreen)
