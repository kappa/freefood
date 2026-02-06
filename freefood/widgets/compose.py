"""Compose block widget for creating posts."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import HorizontalGroup
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
        height: 5;
        border: none;
    }

    ComposeBlock #compose-post-to {
        margin-top: 1;
        height: 1;
        border: none;
        background: $surface;
        color: $text;
    }

    ComposeBlock .compose-actions {
        height: auto;
        margin-top: 1;
    }

    ComposeBlock .compose-actions Button {
        min-width: 8;
        height: 1;
        border: none;
        margin-right: 1;
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

    def __init__(self, default_feeds: str = "") -> None:
        """Initialize compose widget."""
        super().__init__()
        self.is_expanded = False
        self.default_feeds = default_feeds

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
            yield Input(
                value=self.default_feeds,
                placeholder="Post to...",
                id="compose-post-to",
            )
            with HorizontalGroup(classes="compose-actions"):
                yield Button("Cancel", id="compose-cancel")
                yield Button("Post", id="compose-post")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Expand when user starts typing in placeholder."""
        if not self.is_expanded and event.input.id == "compose-placeholder":
            self._expand()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Expand when user presses Enter in placeholder."""
        if not self.is_expanded and event.input.id == "compose-placeholder":
            self._expand()

    def _expand(self) -> None:
        """Expand the compose block and focus the textarea."""
        self.is_expanded = True
        self.refresh(recompose=True)
        # Focus the textarea after recompose
        self.call_after_refresh(self._focus_textarea)

    def _focus_textarea(self) -> None:
        """Focus the textarea after expansion."""
        try:
            textarea = self.query_one("#compose-body", TextArea)
            textarea.focus()
        except Exception:
            pass

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
            feeds = (
                [f.strip() for f in feeds_str.split(",") if f.strip()]
                if feeds_str
                else []
            )
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
