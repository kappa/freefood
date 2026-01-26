"""Compose block widget for creating posts."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input, TextArea


class ComposeBlock(Widget, can_focus=True):
    """Widget for composing new posts."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    DEFAULT_CSS = """
    ComposeBlock {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
        height: auto;
    }

    ComposeBlock #compose-placeholder {
        height: 1;
    }

    ComposeBlock #compose-body {
        min-height: 3;
        max-height: 10;
    }

    ComposeBlock #compose-post-to {
        margin-top: 1;
        height: 1;
    }

    ComposeBlock Horizontal {
        height: auto;
        margin-top: 1;
        align: right middle;
    }

    ComposeBlock Horizontal Button {
        margin-left: 1;
        min-width: 10;
    }

    ComposeBlock #compose-post {
        background: $accent;
    }
    """

    class PostRequested(Message):
        """Request to create a new post."""

        def __init__(self, body: str, feeds: list[str]) -> None:
            self.body = body
            self.feeds = feeds
            super().__init__()

    def __init__(self) -> None:
        """Initialize compose widget."""
        super().__init__()
        self.is_expanded = False

    def compose(self) -> ComposeResult:
        """Create compose widgets."""
        if not self.is_expanded:
            # Collapsed state: just a placeholder
            yield Input(
                placeholder="Write something...",
                id="compose-placeholder",
            )
        else:
            # Expanded state: full compose UI
            yield TextArea(id="compose-body")
            yield Input(placeholder="Post to...", id="compose-post-to")
            with Horizontal():
                yield Button("Cancel", id="compose-cancel")
                yield Button("Post", id="compose-post")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Expand when user starts typing in placeholder."""
        if not self.is_expanded and event.input.id == "compose-placeholder":
            self.is_expanded = True
            self.refresh(recompose=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "compose-cancel":
            self.is_expanded = False
            self.refresh(recompose=True)
        elif event.button.id == "compose-post":
            # Get the body text
            textarea = self.query_one("#compose-body", TextArea)
            body = textarea.text.strip()
            # Validate: body must not be empty
            if not body:
                return
            # Get the feeds
            post_to = self.query_one("#compose-post-to", Input)
            feeds_str = post_to.value.strip()
            feeds = [f.strip() for f in feeds_str.split(",") if f.strip()] if feeds_str else []
            # Emit the message
            self.post_message(self.PostRequested(body, feeds))

    def action_cancel(self) -> None:
        """Cancel/collapse the compose block."""
        if self.is_expanded:
            self.is_expanded = False
            self.refresh(recompose=True)

    def reset(self) -> None:
        """Reset the compose block (collapse and clear)."""
        self.is_expanded = False
        self.refresh(recompose=True)
