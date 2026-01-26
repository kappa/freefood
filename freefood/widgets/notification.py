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

    BINDINGS = [
        ("enter", "enter_post_mode", "Enter notification"),
    ]

    DEFAULT_CSS = """
    NotificationBlock {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
        height: auto;
    }

    NotificationBlock > Vertical {
        height: auto;
    }

    NotificationBlock:focus {
        border: solid $accent;
    }

    NotificationBlock.post-mode {
        border: double $accent;
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
        self.post_mode = False

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
            user_btn.can_focus = self.post_mode
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
                btn.can_focus = self.post_mode
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

    def action_enter_post_mode(self) -> None:
        """Enter post mode, making buttons focusable."""
        self.post_mode = True
        self.add_class("post-mode")
        self.refresh(recompose=True)
        self.call_after_refresh(self._focus_first_button)

    def action_exit_post_mode(self) -> None:
        """Exit post mode, return focus to this block."""
        self.post_mode = False
        self.remove_class("post-mode")
        self.refresh(recompose=True)
        self.focus()

    def _focus_first_button(self) -> None:
        """Focus the first button in this notification."""
        for button in self.query(Button):
            if button.can_focus:
                button.focus()
                return

    def on_key(self, event) -> None:
        """Handle key events for notification post mode navigation."""
        if not self.post_mode:
            return
        focused = self.screen.focused
        if focused is None or focused is self:
            return
        if not self.is_ancestor_of(focused):
            return

        focusable = [w for w in self.query("*") if w.can_focus and w is not self]

        if event.key in ("up", "left", "shift+tab"):
            if focused in focusable:
                idx = focusable.index(focused)
                if idx > 0:
                    focusable[idx - 1].focus()
            event.stop()
        elif event.key in ("down", "right", "tab"):
            if focused in focusable:
                idx = focusable.index(focused)
                if idx < len(focusable) - 1:
                    focusable[idx + 1].focus()
            event.stop()
        elif event.key == "escape":
            self.action_exit_post_mode()
            event.stop()

    def is_ancestor_of(self, widget) -> bool:
        """Check if this widget is an ancestor of the given widget."""
        parent = widget.parent
        while parent is not None:
            if parent is self:
                return True
            parent = parent.parent
        return False
