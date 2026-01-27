"""CommentCompose widget for creating comments."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import HorizontalGroup
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, TextArea


class CommentCompose(Widget, can_focus=True):
    """Widget for composing comments on posts."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("ctrl+enter", "submit", "Submit", show=False),
    ]

    DEFAULT_CSS = """
    CommentCompose {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
        height: auto;
    }

    CommentCompose #comment-body {
        height: 3;
        border: none;
    }

    CommentCompose .comment-actions {
        height: auto;
        margin-top: 1;
    }

    CommentCompose .comment-actions Button {
        min-width: 8;
        height: 1;
        border: none;
        margin-right: 1;
    }

    CommentCompose #comment-submit {
        background: $accent;
    }
    """

    class Cancelled(Message):
        """Emitted when comment compose is cancelled."""

        pass

    class CommentRequested(Message):
        """Emitted when user wants to submit a comment."""

        def __init__(self, post_id: str, body: str) -> None:
            self.post_id = post_id
            self.body = body
            super().__init__()

    def __init__(self, post_id: str) -> None:
        """Initialize comment compose widget."""
        super().__init__()
        self.post_id = post_id

    def compose(self) -> ComposeResult:
        """Create comment compose widgets."""
        yield TextArea(id="comment-body")
        with HorizontalGroup(classes="comment-actions"):
            yield Button("Cancel", id="comment-cancel")
            yield Button("Submit", id="comment-submit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "comment-cancel":
            self.post_message(self.Cancelled())
        elif event.button.id == "comment-submit":
            textarea = self.query_one("#comment-body", TextArea)
            body = textarea.text.strip()
            if body:
                self.post_message(self.CommentRequested(self.post_id, body))

    def action_cancel(self) -> None:
        """Cancel comment composition."""
        self.post_message(self.Cancelled())

    def action_submit(self) -> None:
        """Submit comment."""
        textarea = self.query_one("#comment-body", TextArea)
        body = textarea.text.strip()
        if body:
            self.post_message(self.CommentRequested(self.post_id, body))
