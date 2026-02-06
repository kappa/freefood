"""Tests for NotificationsScreen behavior."""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from textual.app import App
from textual.widgets import Button, Static

from freefood.models import HistoryEntry, Notification, Post, User, View
from freefood.screens.notifications import NotificationsScreen
from freefood.state import AppState
from freefood.widgets.menu import MenuBar
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


class MockApp(App):
    """App stub with screen tracking for navigation tests."""

    def __init__(self, state: AppState | None = None, api: object | None = None):
        super().__init__()
        self.state = state or AppState()
        self.api = api
        self.pushed_screens: list = []
        self._original_push = None

    async def on_mount(self) -> None:
        self._original_push = self.push_screen

        def tracking_push(screen, *args, **kwargs):
            self.pushed_screens.append(screen)
            return self._original_push(screen, *args, **kwargs)

        self.push_screen = tracking_push  # type: ignore[assignment]


def make_post(
    id: str = "p1",
    body: str = "Test post body",
) -> Post:
    """Create a test post for notification tests."""
    now = datetime.now()
    return Post(
        id=id,
        body=body,
        author=make_user(),
        groups=[],
        created_at=now,
        updated_at=now,
        comments=[],
        omitted_comments=0,
        omitted_comments_offset=0,
        omitted_comment_likes=0,
        omitted_likes=0,
        likes=[],
    )


class TestNotificationsStateFallback:
    """Tests for state property fallback."""

    @pytest.mark.asyncio
    async def test_state_falls_back_to_app_state(self):
        """State should fall back to app.state when _state is None."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(return_value=[])
        api.get_unread_notifications_count = AsyncMock(return_value=0)
        app_state = AppState(current_view=View.NOTIFICATIONS)
        app = MockApp(state=app_state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state=None))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            assert screen.state is app_state


class TestNotificationsErrorHandling:
    """Tests for error handling paths."""

    @pytest.mark.asyncio
    async def test_shows_error_when_api_is_none(self):
        """Should show error when api is None."""
        state = AppState(current_view=View.NOTIFICATIONS)
        app = MockApp(state=state, api=None)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            error = screen.query_one(".error", Static)
            assert "Not connected" in str(error.render())

    @pytest.mark.asyncio
    async def test_shows_error_when_api_raises(self):
        """Should show error when api.get_notifications raises."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(side_effect=Exception("API error"))
        state = AppState(current_view=View.NOTIFICATIONS)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            error = screen.query_one(".error", Static)
            assert "API error" in str(error.render())


class TestNotificationsFocusActions:
    """Tests for focus actions."""

    @pytest.mark.asyncio
    async def test_action_focus_menu(self):
        """action_focus_menu should focus the menu bar button."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(return_value=[make_notification()])
        api.get_unread_notifications_count = AsyncMock(return_value=0)
        state = AppState(current_view=View.NOTIFICATIONS)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            screen.action_focus_menu()
            await pilot.pause()

            focused = app.focused
            assert isinstance(focused, Button)

    @pytest.mark.asyncio
    async def test_action_focus_list_with_notifications(self):
        """action_focus_list should focus first NotificationBlock."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(return_value=[make_notification()])
        api.get_unread_notifications_count = AsyncMock(return_value=0)
        state = AppState(current_view=View.NOTIFICATIONS)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            screen.action_focus_list()
            await pilot.pause()

            focused = app.focused
            assert isinstance(focused, NotificationBlock)

    @pytest.mark.asyncio
    async def test_action_focus_list_focuses_first_block(self):
        """action_focus_list should focus the first NotificationBlock when present."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(return_value=[make_notification()])
        api.get_unread_notifications_count = AsyncMock(return_value=0)
        state = AppState(current_view=View.NOTIFICATIONS)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            # First focus menu, then use action_focus_list to refocus
            screen.action_focus_menu()
            await pilot.pause()
            screen.action_focus_list()
            await pilot.pause()

            focused = app.focused
            assert isinstance(focused, NotificationBlock)


class TestNotificationsRefresh:
    """Tests for the refresh action."""

    @pytest.mark.asyncio
    async def test_action_refresh_triggers_reload(self):
        """action_refresh should trigger refresh_content."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(return_value=[make_notification()])
        api.get_unread_notifications_count = AsyncMock(return_value=0)
        state = AppState(current_view=View.NOTIFICATIONS)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            screen.action_refresh()
            await pilot.pause()

            # Called twice: once on mount and once on refresh
            assert api.get_notifications.call_count == 2


class TestNotificationsMenuNavigation:
    """Tests for menu bar view selection navigation."""

    @pytest.mark.asyncio
    async def test_selecting_search_navigates(self):
        """Selecting SEARCH view should push SearchScreen."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(return_value=[])
        api.get_unread_notifications_count = AsyncMock(return_value=0)
        state = AppState(current_view=View.NOTIFICATIONS)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.SEARCH))
            await pilot.pause()

            from freefood.screens.search import SearchScreen

            assert any(isinstance(s, SearchScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_selecting_notifications_is_noop(self):
        """Selecting NOTIFICATIONS view should do nothing (already there)."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(return_value=[])
        api.get_unread_notifications_count = AsyncMock(return_value=0)
        state = AppState(current_view=View.NOTIFICATIONS)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)

            # Record count before
            count_before = len(app.pushed_screens)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.NOTIFICATIONS))
            await pilot.pause()

            # No new screens should have been pushed
            assert len(app.pushed_screens) == count_before

    @pytest.mark.asyncio
    async def test_selecting_errors_navigates(self):
        """Selecting ERRORS view should push ErrorsScreen."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(return_value=[])
        api.get_unread_notifications_count = AsyncMock(return_value=0)
        state = AppState(current_view=View.NOTIFICATIONS)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.ERRORS))
            await pilot.pause()

            from freefood.screens.errors import ErrorsScreen

            assert any(isinstance(s, ErrorsScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_selecting_home_navigates_to_feed(self):
        """Selecting HOME view should push FeedScreen."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(return_value=[])
        api.get_unread_notifications_count = AsyncMock(return_value=0)
        state = AppState(current_view=View.NOTIFICATIONS)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.HOME))
            await pilot.pause()

            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_selecting_directs_navigates_to_feed(self):
        """Selecting DIRECTS view should push FeedScreen with navigate_to."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(return_value=[])
        api.get_unread_notifications_count = AsyncMock(return_value=0)
        state = AppState(current_view=View.NOTIFICATIONS)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            screen.on_menu_bar_view_selected(MenuBar.ViewSelected(View.DIRECTS))
            await pilot.pause()

            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)
            assert state.current_view == View.DIRECTS


class TestNotificationsBackNavigation:
    """Tests for back navigation via menu bar."""

    @pytest.mark.asyncio
    async def test_back_with_no_history_does_nothing(self):
        """Back with empty history should do nothing."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(return_value=[])
        api.get_unread_notifications_count = AsyncMock(return_value=0)
        state = AppState(current_view=View.NOTIFICATIONS)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            # Still on NotificationsScreen
            assert isinstance(app.screen, NotificationsScreen)

    @pytest.mark.asyncio
    async def test_back_to_home_pushes_feed_screen(self):
        """Back to HOME should push FeedScreen."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(return_value=[])
        api.get_unread_notifications_count = AsyncMock(return_value=0)
        state = AppState(current_view=View.NOTIFICATIONS)
        state.history.append(
            HistoryEntry(view=View.HOME, target=None, scroll_position=0)
        )
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            from freefood.screens.feed import FeedScreen

            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)
            assert state.current_view == View.HOME

    @pytest.mark.asyncio
    async def test_back_to_search_pushes_search_screen(self):
        """Back to SEARCH should push SearchScreen."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(return_value=[])
        api.get_unread_notifications_count = AsyncMock(return_value=0)
        state = AppState(current_view=View.NOTIFICATIONS)
        state.history.append(
            HistoryEntry(view=View.SEARCH, target=None, scroll_position=0, query="test")
        )
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            from freefood.screens.search import SearchScreen

            assert any(isinstance(s, SearchScreen) for s in app.pushed_screens)
            assert state.current_view == View.SEARCH
            assert state.search_query == "test"

    @pytest.mark.asyncio
    async def test_back_to_notifications_pushes_self(self):
        """Back to NOTIFICATIONS should push new NotificationsScreen."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(return_value=[])
        api.get_unread_notifications_count = AsyncMock(return_value=0)
        state = AppState(current_view=View.NOTIFICATIONS)
        state.history.append(
            HistoryEntry(view=View.NOTIFICATIONS, target=None, scroll_position=0)
        )
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            assert any(isinstance(s, NotificationsScreen) for s in app.pushed_screens)
            assert state.current_view == View.NOTIFICATIONS

    @pytest.mark.asyncio
    async def test_back_restores_target(self):
        """Back should restore current_target from history entry."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(return_value=[])
        api.get_unread_notifications_count = AsyncMock(return_value=0)
        state = AppState(current_view=View.NOTIFICATIONS)
        state.history.append(
            HistoryEntry(view=View.USER_FEED, target="bob", scroll_position=0)
        )
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            screen.on_menu_bar_back_requested(MenuBar.BackRequested())
            await pilot.pause()

            assert state.current_view == View.USER_FEED
            assert state.current_target == "bob"


class TestNotificationsPostClickErrors:
    """Tests for post click error handling."""

    @pytest.mark.asyncio
    async def test_post_click_with_no_api_shows_error(self):
        """PostClicked when api is None should show error banner."""
        state = AppState(current_view=View.NOTIFICATIONS)
        # Need a working API for initial load, then set to None
        initial_api = AsyncMock()
        initial_api.get_notifications = AsyncMock(return_value=[make_notification()])
        initial_api.get_unread_notifications_count = AsyncMock(return_value=0)
        app = MockApp(state=state, api=initial_api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            # Now set api to None
            app.api = None
            await screen.on_notification_block_post_clicked(
                NotificationBlock.PostClicked("p1")
            )
            await pilot.pause()

            # Error banner should be visible
            banner = screen.query_one("#error-banner", Static)
            assert "visible" in banner.classes

    @pytest.mark.asyncio
    async def test_post_click_with_api_error_shows_error(self):
        """PostClicked when api raises should show error banner."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(return_value=[make_notification()])
        api.get_unread_notifications_count = AsyncMock(return_value=0)
        api.get_post = AsyncMock(side_effect=Exception("Post not found"))
        state = AppState(current_view=View.NOTIFICATIONS)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            await screen.on_notification_block_post_clicked(
                NotificationBlock.PostClicked("p1")
            )
            await pilot.pause()

            banner = screen.query_one("#error-banner", Static)
            assert "visible" in banner.classes


class TestNotificationsGroupClick:
    """Tests for group user click navigation."""

    @pytest.mark.asyncio
    async def test_group_click_navigates_to_group_feed(self):
        """UserClicked with group type should navigate to GROUP_FEED."""
        api = AsyncMock()
        api.get_notifications = AsyncMock(return_value=[make_notification()])
        api.get_unread_notifications_count = AsyncMock(return_value=0)
        state = AppState(current_view=View.NOTIFICATIONS)
        app = MockApp(state=state, api=api)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.push_screen(NotificationsScreen(state))
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, NotificationsScreen)
            screen.on_notification_block_user_clicked(
                NotificationBlock.UserClicked("news", "group")
            )
            await pilot.pause()

            assert state.current_view == View.GROUP_FEED
            assert state.current_target == "news"
