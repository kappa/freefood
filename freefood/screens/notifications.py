"""Notifications screen for displaying notification events."""

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Static

from freefood.models import Notification, View
from freefood.screens.base import BaseScreen
from freefood.state import AppState
from freefood.widgets.menu import MenuBar
from freefood.widgets.notification import NotificationBlock


class NotificationsScreen(BaseScreen):
    """Screen for displaying notifications."""

    BINDINGS = [
        ("escape", "focus_menu", "Menu"),
        ("enter", "focus_list", "Notifications"),
        ("f5", "refresh", "Refresh"),
    ]

    CSS = """
    NotificationsScreen {
        layout: vertical;
    }

    #notifications-container {
        height: 1fr;
        padding: 0 1;
    }

    #error-banner {
        background: $error;
        color: $text;
        padding: 0 1;
        display: none;
    }

    #error-banner.visible {
        display: block;
    }
    """

    def __init__(self, state: AppState | None = None) -> None:
        super().__init__()
        self._state = state
        self.notifications: list[Notification] = []

    @property
    def state(self) -> AppState:
        if self._state is not None:
            return self._state
        return self.app.state

    def compose(self) -> ComposeResult:
        yield MenuBar(self.state.current_view)
        yield Static("", id="error-banner")
        with ScrollableContainer(id="notifications-container"):
            yield Static("Loading notifications...", classes="loading")

    async def on_mount(self) -> None:
        await self.refresh_content()

    async def refresh_content(self) -> None:
        container = self.query_one("#notifications-container")
        container.remove_children()
        container.mount(Static("Loading notifications...", classes="loading"))

        try:
            api = self.api
            self.notifications = await api.get_notifications()
            container.remove_children()

            try:
                count = await api.get_unread_notifications_count()
                menu = self.query_one(MenuBar)
                menu.set_notifications_count(count)
            except Exception:
                pass

            if not self.notifications:
                container.mount(
                    Static(
                        "No notifications", id="notifications-empty", classes="loading"
                    )
                )
                return

            for notif in self.notifications:
                container.mount(NotificationBlock(notif))
        except Exception as e:
            container.remove_children()
            container.mount(
                Static(f"Failed to load: {e}\nPress F5 to retry", classes="error")
            )

    def action_focus_menu(self) -> None:
        menu = self.query_one(MenuBar)
        menu.focus_current_view_button()

    def action_focus_list(self) -> None:
        container = self.query_one("#notifications-container")
        first = container.query(NotificationBlock).first()
        if first:
            first.focus()

    def action_refresh(self) -> None:
        self.run_worker(self.refresh_content())

    def on_menu_bar_view_selected(self, message: MenuBar.ViewSelected) -> None:
        message.stop()
        if message.view == View.NOTIFICATIONS:
            self.action_refresh()
            return
        self.state.navigate_to(message.view)
        self.push_screen_for_view(message.view)

    def on_menu_bar_back_requested(self, message: MenuBar.BackRequested) -> None:
        message.stop()
        if not self.navigate_back():
            self.notify("No history")

    def on_notification_block_user_clicked(
        self, message: NotificationBlock.UserClicked
    ) -> None:
        """Handle navigation to a user or group feed."""
        view = View.GROUP_FEED if message.user_type == "group" else View.USER_FEED
        self.state.navigate_to(view, target=message.username)
        self.push_screen_for_view(view)

    async def on_notification_block_post_clicked(
        self, message: NotificationBlock.PostClicked
    ) -> None:
        """Handle navigation to a single post."""
        try:
            post = await self.api.get_post(message.post_id)
            from freefood.screens.post import PostScreen

            self.app.push_screen(PostScreen(self.state, post=post))
        except Exception as e:
            self.show_error("Failed to load post", e)
