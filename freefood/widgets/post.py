"""Post block widget for displaying posts."""

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal, HorizontalGroup, Vertical, VerticalGroup
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, Button

from freefood.models import Post, Comment
from freefood.search import highlight_text
from rich.markup import escape


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


def build_user_link_id(scope: str, user_type: str, username: str) -> str:
    """Build a stable id for user/group links."""
    return f"user-link-{scope}-{user_type}-{username}"


class CommentBlock(Widget):
    """Widget displaying a single comment. Focusable in post mode."""

    DEFAULT_CSS = """
    CommentBlock {
        margin-top: 1;
        padding-left: 2;
        border-left: solid $primary;
        height: auto;
    }

    CommentBlock:focus {
        background: $surface-lighten-2;
        border-left: solid $accent;
    }

    CommentBlock #comment-meta-prefix {
        width: 3;
    }
    """

    MAX_COMMENT_LINES = 10

    def __init__(
        self,
        comment: Comment,
        post_mode: bool = False,
        highlight_terms: list[str] | None = None,
    ) -> None:
        """Initialize comment widget."""
        super().__init__()
        self.comment = comment
        self.can_focus = post_mode
        self.highlight_terms = highlight_terms or []

    def _format_body(self) -> str:
        """Format comment body with truncation and optional highlighting."""
        lines = self.comment.body.split("\n")
        if len(lines) > self.MAX_COMMENT_LINES:
            body = "\n".join(lines[: self.MAX_COMMENT_LINES]) + "\n[show more...]"
        else:
            body = self.comment.body

        if self.highlight_terms:
            return highlight_text(body, self.highlight_terms)
        return body

    def compose(self) -> ComposeResult:
        """Create comment widgets."""
        body = self._format_body()
        likes_str = f"[{self.comment.likes}♥]" if self.comment.likes else "[0♥]"
        if self.highlight_terms:
            likes_str = escape(likes_str)

        with VerticalGroup(id="comment-container"):
            yield Static(
                f"{likes_str} {body}",
                markup=bool(self.highlight_terms),
            )
            with HorizontalGroup(id="comment-meta"):
                yield Static("-- ", id="comment-meta-prefix")
                if self.comment.author is not None:
                    author_btn = Button(
                        f"@{self.comment.author.username}",
                        id=build_user_link_id(
                            "comment",
                            self.comment.author.type,
                            self.comment.author.username,
                        ),
                        classes="user-link",
                    )
                    author_btn.can_focus = self.can_focus
                    yield author_btn
                else:
                    yield Static("@unknown")


class PostBlock(Widget, can_focus=True):
    """Widget displaying a single post."""

    BINDINGS = [
        ("enter", "enter_post_mode", "Enter post"),
        # Note: up/down removed - they should scroll the feed, not change selection
        # Tab/Shift-Tab move between posts
        # Escape is handled by on_key when in post_mode
        # When not in post_mode, escape bubbles to FeedScreen to focus menu
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

    PostBlock .user-link {
        border: none;
        height: 1;
        padding: 0;
        background: transparent;
        color: $accent;
        text-style: underline;
        min-width: 0;
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

    PostBlock .more-comments {
        text-align: center;
        color: $text-muted;
        margin: 1 0;
        height: 1;
        border: none;
        width: 100%;
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

    PostBlock #post-likes-prefix {
        width: 2;
    }

    PostBlock .likes-sep {
        width: 2;
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

    class UserClicked(Message):
        """Request to navigate to a user or group feed."""

        def __init__(self, username: str, user_type: str) -> None:
            self.username = username
            self.user_type = user_type
            super().__init__()

    def __init__(self, post: Post, highlight_terms: list[str] | None = None) -> None:
        """Initialize post widget."""
        super().__init__()
        self.post = post
        self.body_expanded = False
        self.comments_expanded = False
        self.post_mode = False  # When True, buttons are focusable
        self.highlight_terms = highlight_terms or []

    def compose(self) -> ComposeResult:
        """Create post widgets."""
        with Vertical():
            # Header
            with HorizontalGroup(id="post-header", classes="post-header"):
                author = self.post.author
                if author is not None:
                    author_btn = Button(
                        f"@{author.username}",
                        id=build_user_link_id("header", author.type, author.username),
                        classes="user-link",
                    )
                    author_btn.can_focus = self.post_mode
                    yield author_btn
                else:
                    yield Static("@unknown")

                if self.post.groups:
                    yield Static(" wrote in ")
                    for idx, group in enumerate(self.post.groups):
                        if idx > 0:
                            yield Static(", ")
                        group_btn = Button(
                            f"@{group.username}",
                            id=build_user_link_id("header", group.type, group.username),
                            classes="user-link",
                        )
                        group_btn.can_focus = self.post_mode
                        yield group_btn
                    yield Static(":")
                else:
                    yield Static(" wrote:")

            # Body
            yield Static(
                self._format_body(),
                classes="post-body",
                markup=bool(self.highlight_terms),
            )
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
            yield from self._render_likes()

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
            body = f"{truncated}\n[show more...]"
        else:
            body = self.post.body

        if self.highlight_terms:
            return highlight_text(body, self.highlight_terms)
        return body

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
        """Render comments section.

        Comments are displayed with the 'more comments' button inserted at the
        position specified by omittedCommentsOffset. The offset indicates where
        the omitted comments gap is in the full comment list.

        Example: comments=[c1,c2,c3], omittedComments=10, omittedCommentsOffset=1
        Display: c1, [10 more comments with M likes], c2, c3
        """
        comments = self.post.comments
        omitted = self.post.omitted_comments
        offset = self.post.omitted_comments_offset
        omitted_likes = self.post.omitted_comment_likes

        if not comments and omitted == 0:
            return

        # Track if we've yielded the more-comments button
        button_yielded = False

        # Render comments with the 'more comments' button at the correct offset
        for i, comment in enumerate(comments):
            # Insert 'more comments' button at the offset position
            if omitted > 0 and not self.comments_expanded and i == offset and not button_yielded:
                btn = Button(
                    f"── {omitted} more comments with {omitted_likes} likes ──",
                    id="btn-more-comments",
                    classes="more-comments",
                )
                btn.can_focus = self.post_mode
                yield btn
                button_yielded = True
            yield CommentBlock(
                comment,
                post_mode=self.post_mode,
                highlight_terms=self.highlight_terms,
            )


        # If offset equals len(comments) and button not yet yielded, button goes at the end
        if omitted > 0 and not self.comments_expanded and offset >= len(comments) and not button_yielded:
            btn = Button(
                f"── {omitted} more comments with {omitted_likes} likes ──",
                id="btn-more-comments",
                classes="more-comments",
            )
            btn.can_focus = self.post_mode
            yield btn

    def _render_likes(self):
        """Render likes line with clickable usernames."""
        likes = self.post.likes
        if not likes:
            return

        displayed = likes[:3]
        with HorizontalGroup(id="post-likes", classes="post-likes"):
            yield Static("♥ ", id="post-likes-prefix")
            for idx, user in enumerate(displayed):
                btn = Button(
                    f"@{user.username}",
                    id=build_user_link_id("like", user.type, user.username),
                    classes="user-link",
                )
                btn.can_focus = self.post_mode
                yield btn
                if idx < len(displayed) - 1:
                    yield Static(", ", classes="likes-sep")

            if len(likes) <= 3:
                yield Static(" liked this")
            else:
                others = len(likes) - 3 + self.post.omitted_likes
                yield Static(f" and {others} others liked this")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id and event.button.id.startswith("user-link-"):
            remainder = event.button.id[len("user-link-") :]
            parts = remainder.split("-", 2)
            if len(parts) == 3:
                _, user_type, username = parts
                self.post_message(self.UserClicked(username, user_type))
            return

        if event.button.id == "show-more-body":
            self.body_expanded = True
            self.refresh(recompose=True)
        elif event.button.id == "btn-more-comments":
            self.comments_expanded = True
            self.post_message(self.ExpandComments(self.post))
        elif event.button.id == "btn-like":
            self.post_message(self.LikeRequested(self.post))
        elif event.button.id == "btn-hide":
            self.post_message(self.HideRequested(self.post))

    def focus_comment_at(self, index: int) -> bool:
        """Focus the comment at a given index if available."""
        comments = list(self.query(CommentBlock))
        if comments:
            idx = max(0, min(index, len(comments) - 1))
            self.app.set_focus(comments[idx])
            return True
        return False

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

        # Get all focusable children within this post
        focusable = [w for w in self.query("*") if w.can_focus and w is not self]

        if event.key in ("up", "left", "shift+tab"):
            # Move to previous focusable within this post
            if focused in focusable:
                idx = focusable.index(focused)
                if idx > 0:
                    focusable[idx - 1].focus()
                # else: at first element, stay put
            event.stop()
        elif event.key in ("down", "right", "tab"):
            # Move to next focusable within this post
            if focused in focusable:
                idx = focusable.index(focused)
                if idx < len(focusable) - 1:
                    focusable[idx + 1].focus()
                # else: at last element, stay put
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
