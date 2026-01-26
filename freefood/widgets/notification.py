"""Notification block widget for displaying notifications."""

from textual.app import ComposeResult
from textual.containers import HorizontalGroup, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Static

from freefood.models import Notification
from freefood.widgets.post import build_user_link_id


class NotificationBlock(Widget, can_focus=True):
    """Widget displaying a single notification."""

    DEFAULT_CSS = """
    NotificationBlock {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
        height: auto;
    }

    NotificationBlock:focus {
        border: solid $accent;
    }

    NotificationBlock .user-link {
        border: none;
        height: 1;
        padding: 0;
        background: transparent;
        color: $accent;
        text-style: underline;
        min-width: 0;
    }

    NotificationBlock .post-link {
        border: none;
        height: 1;
        padding: 0;
        background: transparent;
        color: $accent;
        text-style: underline;
    }
    """

    class UserClicked(Message):
        """Request to navigate to a user or group feed."""

        def __init__(self, username: str, user_type: str) -> None:
            self.username = username
            self.user_type = user_type
            super().__init__()

    class PostClicked(Message):
        """Request to navigate to a post."""

        def __init__(self, post_id: str) -> None:
            self.post_id = post_id
            super().__init__()

    def __init__(self, notification: Notification) -> None:
        super().__init__()
        self.notification = notification

    def _format_tail(self) -> str:
        """Format notification text after username."""
        event_type = self.notification.event_type

        templates = {
            "direct_comment": "commented on your post",
            "post_comment": "commented on a post",
            "mention_in_post": "mentioned you in a post",
            "mention_in_comment": "mentioned you in a comment",
            "mention_comment_to": "mentioned you in a comment",
            "post_like": "liked your post",
            "subscription": "subscribed to you",
            "backlink_in_post": "mentioned your post",
        }

        return templates.get(event_type, event_type)

    def compose(self) -> ComposeResult:
        """Create notification widgets."""
        user = self.notification.created_user
        if user is not None:
            user_btn = Button(
                f"@{user.username}",
                id=build_user_link_id("notification", user.type, user.username),
                classes="user-link",
            )
            user_btn.can_focus = True
            tail = self._format_tail()
        else:
            user_btn = Button("@unknown", classes="user-link")
            user_btn.can_focus = False
            tail = self._format_tail()

        with Vertical():
            with HorizontalGroup():
                yield user_btn
                yield Static(f" {tail}")
            if self.notification.post_id:
                btn = Button("View post", id="btn-view-post", classes="post-link")
                btn.can_focus = True
                yield btn

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id and event.button.id.startswith("user-link-"):
            remainder = event.button.id[len("user-link-") :]
            parts = remainder.split("-", 2)
            if len(parts) == 3:
                _, user_type, username = parts
                self.post_message(self.UserClicked(username, user_type))
            return
        if event.button.id == "btn-view-post" and self.notification.post_id:
            self.post_message(self.PostClicked(self.notification.post_id))
