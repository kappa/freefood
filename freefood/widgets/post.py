"""Post block widget for displaying posts."""

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, Button

from freefood.models import Post, Comment


def format_time_ago(dt: datetime) -> str:
    """Format datetime as relative time."""
    now = datetime.now()
    diff = now - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        mins = int(seconds / 60)
        return f"{mins}m ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}h ago"
    else:
        days = int(seconds / 86400)
        return f"{days}d ago"


class PostBlock(Widget, can_focus=True):
    """Widget displaying a single post."""

    BINDINGS = [
        ("enter", "enter_post_mode", "Enter post"),
        ("up", "focus_previous", "Previous"),
        ("down", "focus_next", "Next"),
        ("escape", "exit_post_mode", "Back to feed"),
    ]

    DEFAULT_CSS = """
    PostBlock {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
        height: auto;
    }

    PostBlock > Vertical {
        height: auto;
    }

    PostBlock:focus {
        border: solid $accent;
    }

    PostBlock.post-mode {
        border: double $accent;
    }

    PostBlock .post-header {
        color: $text;
        text-style: bold;
    }

    PostBlock .post-body {
        margin: 1 0;
    }

    PostBlock .post-meta {
        color: $text-muted;
    }

    PostBlock .post-likes {
        color: $text-muted;
        margin-top: 1;
    }

    PostBlock .comment {
        margin-top: 1;
        padding-left: 2;
        border-left: solid $primary;
    }

    PostBlock .comment-likes {
        color: $error;
    }

    PostBlock .more-comments {
        text-align: center;
        color: $text-muted;
        margin: 1 0;
    }

    PostBlock .post-actions {
        height: auto;
        margin-top: 1;
    }

    PostBlock .post-actions Button {
        min-width: 8;
        height: 1;
        border: none;
        margin-right: 1;
    }

    PostBlock .show-more {
        color: $text-muted;
        margin: 0;
    }

    PostBlock Button:focus {
        background: $accent;
    }
    """

    MAX_BODY_LINES = 50
    MAX_COMMENT_LINES = 10

    class Selected(Message):
        """Message sent when post is selected."""

        def __init__(self, post: Post) -> None:
            self.post = post
            super().__init__()

    class ExpandComments(Message):
        """Request to load all comments for a post."""

        def __init__(self, post: Post) -> None:
            self.post = post
            super().__init__()

    class LikeRequested(Message):
        """Request to like/unlike post."""

        def __init__(self, post: Post) -> None:
            self.post = post
            super().__init__()

    class HideRequested(Message):
        """Request to hide/unhide post."""

        def __init__(self, post: Post) -> None:
            self.post = post
            super().__init__()

    def __init__(self, post: Post) -> None:
        """Initialize post widget."""
        super().__init__()
        self.post = post
        self.body_expanded = False
        self.comments_expanded = False
        self.post_mode = False  # When True, buttons are focusable

    def compose(self) -> ComposeResult:
        """Create post widgets."""
        with Vertical():
            # Header
            yield Static(self._format_header(), classes="post-header")

            # Body
            yield Static(self._format_body(), classes="post-body")
            if self._body_is_truncated():
                btn = Button("Show more...", id="show-more-body", classes="show-more")
                btn.can_focus = self.post_mode
                yield btn

            # Timestamp
            yield Static(format_time_ago(self.post.created_at), classes="post-meta")

            # Action buttons on separate line
            with Horizontal(classes="post-actions"):
                btn_comment = Button("Comment", id="btn-comment")
                btn_comment.can_focus = self.post_mode
                yield btn_comment
                like_label = "Unlike" if self.post.is_liked else "Like"
                btn_like = Button(f"♥ {like_label}", id="btn-like")
                btn_like.can_focus = self.post_mode
                yield btn_like
                hide_label = "Unhide" if self.post.is_hidden else "Hide"
                btn_hide = Button(hide_label, id="btn-hide")
                btn_hide.can_focus = self.post_mode
                yield btn_hide
                if self.post.is_own:
                    btn_edit = Button("Edit", id="btn-edit")
                    btn_edit.can_focus = self.post_mode
                    yield btn_edit
                    btn_delete = Button("Delete", id="btn-delete")
                    btn_delete.can_focus = self.post_mode
                    yield btn_delete

            # Likes
            if self.post.likes:
                yield Static(self._format_likes(), classes="post-likes")

            # Comments
            yield from self._render_comments()

    def _body_is_truncated(self) -> bool:
        """Check if body exceeds max lines."""
        lines = self.post.body.split("\n")
        return len(lines) > self.MAX_BODY_LINES and not self.body_expanded

    def _format_header(self) -> str:
        """Format post header."""
        author = f"@{self.post.author.username}" if self.post.author else "@unknown"
        if self.post.groups:
            groups = ", ".join(f"@{g.username}" for g in self.post.groups)
            return f"{author} wrote in {groups}:"
        return f"{author} wrote:"

    def _format_body(self) -> str:
        """Format post body with truncation."""
        lines = self.post.body.split("\n")
        if len(lines) > self.MAX_BODY_LINES and not self.body_expanded:
            truncated = "\n".join(lines[: self.MAX_BODY_LINES])
            return f"{truncated}\n[show more...]"
        return self.post.body

    def _format_likes(self) -> str:
        """Format likes line."""
        likes = self.post.likes
        if len(likes) <= 3:
            names = ", ".join(f"@{u.username}" for u in likes)
            return f"♥ {names} liked this"
        else:
            names = ", ".join(f"@{u.username}" for u in likes[:3])
            others = len(likes) - 3 + self.post.omitted_likes
            return f"♥ {names} and {others} others liked this"

    def _render_comments(self):
        """Render comments section."""
        comments = self.post.comments
        omitted = self.post.omitted_comments
        total = len(comments) + omitted

        if total == 0:
            return

        # If there are omitted comments, show indicator at top
        if omitted > 0 and not self.comments_expanded:
            yield Static(
                f"── {omitted} earlier comments ──",
                classes="more-comments",
            )

        # Show first 2 and last 2 if we have many local comments
        if len(comments) <= 4 or self.comments_expanded:
            for comment in comments:
                yield self._render_comment(comment)
        else:
            # First 2
            for comment in comments[:2]:
                yield self._render_comment(comment)

            # Middle expander
            middle_count = len(comments) - 4
            yield Static(
                f"── {middle_count} more comments ──",
                classes="more-comments",
            )

            # Last 2
            for comment in comments[-2:]:
                yield self._render_comment(comment)

    def _render_comment(self, comment: Comment) -> Static:
        """Render a single comment."""
        lines = comment.body.split("\n")
        if len(lines) > self.MAX_COMMENT_LINES:
            body = "\n".join(lines[: self.MAX_COMMENT_LINES]) + "\n[show more...]"
        else:
            body = comment.body

        likes_str = f"[{comment.likes}♥]" if comment.likes else "[0♥]"
        author_name = comment.author.username if comment.author else "unknown"
        text = f"{likes_str} {body} -- @{author_name}"
        return Static(text, classes="comment")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "show-more-body":
            self.body_expanded = True
            self.refresh(recompose=True)
        elif event.button.id == "show-more-comments":
            self.comments_expanded = True
            self.post_message(self.ExpandComments(self.post))
        elif event.button.id == "btn-like":
            self.post_message(self.LikeRequested(self.post))
        elif event.button.id == "btn-hide":
            self.post_message(self.HideRequested(self.post))

    def action_enter_post_mode(self) -> None:
        """Enter post mode, making buttons focusable."""
        self.post_mode = True
        self.add_class("post-mode")
        self.refresh(recompose=True)
        # Focus first button after recompose
        self.call_after_refresh(self._focus_first_button)

    def _focus_first_button(self) -> None:
        """Focus the first button in this post."""
        buttons = list(self.query(Button))
        if buttons:
            buttons[0].focus()

    def action_focus_previous(self) -> None:
        """Focus previous post (when PostBlock has focus)."""
        # Find previous PostBlock sibling
        posts = list(self.screen.query(PostBlock))
        try:
            idx = posts.index(self)
            if idx > 0:
                posts[idx - 1].focus()
        except (ValueError, IndexError):
            pass

    def action_focus_next(self) -> None:
        """Focus next post (when PostBlock has focus)."""
        # Find next PostBlock sibling
        posts = list(self.screen.query(PostBlock))
        try:
            idx = posts.index(self)
            if idx < len(posts) - 1:
                posts[idx + 1].focus()
        except (ValueError, IndexError):
            pass

    def action_exit_post_mode(self) -> None:
        """Exit post mode, return focus to this post block."""
        self.post_mode = False
        self.remove_class("post-mode")
        self.refresh(recompose=True)
        self.focus()

    def on_key(self, event) -> None:
        """Handle key events for post mode navigation."""
        if not self.post_mode:
            return
        # When in post mode and a child button has focus, handle navigation
        focused = self.screen.focused
        if focused is None or focused is self:
            return
        # Check if focused widget is inside this PostBlock
        if not self.is_ancestor_of(focused):
            return
        if event.key == "up":
            self.screen.focus_previous()
            event.stop()
        elif event.key == "down":
            self.screen.focus_next()
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
