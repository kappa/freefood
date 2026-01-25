"""Post block widget for displaying posts."""

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

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

    DEFAULT_CSS = """
    PostBlock {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
        height: auto;
    }

    PostBlock:focus {
        border: solid $accent;
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
    """

    MAX_BODY_LINES = 50
    MAX_COMMENT_LINES = 10

    class Selected(Message):
        """Message sent when post is selected."""

        def __init__(self, post: Post) -> None:
            self.post = post
            super().__init__()

    def __init__(self, post: Post) -> None:
        """Initialize post widget."""
        super().__init__()
        self.post = post
        self.body_expanded = False
        self.comments_expanded = False

    def compose(self) -> ComposeResult:
        """Create post widgets."""
        with Vertical():
            # Header
            header = self._format_header()
            yield Static(header, classes="post-header")

            # Body
            body = self._format_body()
            yield Static(body, classes="post-body")

            # Meta (time, actions placeholder)
            meta = format_time_ago(self.post.created_at)
            yield Static(meta, classes="post-meta")

            # Likes
            if self.post.likes:
                likes_text = self._format_likes()
                yield Static(likes_text, classes="post-likes")

            # Comments
            yield from self._render_comments()

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
        total = len(comments) + self.post.omitted_comments

        if total == 0:
            return

        # Show first 2 and last 2
        if len(comments) <= 4 or self.comments_expanded:
            for comment in comments:
                yield self._render_comment(comment)
        else:
            # First 2
            for comment in comments[:2]:
                yield self._render_comment(comment)

            # Middle expander
            middle_count = total - 4
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
