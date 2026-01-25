"""Feed screen for displaying posts."""

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.screen import Screen
from textual.widgets import Static

from freefood.models import View, Post
from freefood.widgets.menu import MenuBar
from freefood.widgets.post import PostBlock


class FeedScreen(Screen):
    """Screen for displaying feed content."""

    BINDINGS = [
        ("escape", "focus_menu", "Menu"),
        ("f5", "refresh", "Refresh"),
    ]

    CSS = """
    FeedScreen {
        layout: vertical;
    }

    #feed-container {
        height: 1fr;
        padding: 0 1;
    }
    """

    def __init__(self, view: View = View.HOME) -> None:
        """Initialize feed screen."""
        super().__init__()
        self.current_view = view
        self.posts: list[Post] = []

    def compose(self) -> ComposeResult:
        """Create feed screen widgets."""
        yield MenuBar(self.current_view)
        with ScrollableContainer(id="feed-container"):
            yield Static("Loading feed...", classes="loading")

    async def on_mount(self) -> None:
        """Load feed on mount."""
        await self.refresh_content()

    async def refresh_content(self) -> None:
        """Refresh feed content."""
        container = self.query_one("#feed-container")
        container.remove_children()
        container.mount(Static("Loading feed...", classes="loading"))

        try:
            api = self.app.api
            if api is None:
                raise Exception("Not connected")

            if self.current_view == View.HOME:
                self.posts = await api.get_home_feed()
            elif self.current_view == View.DIRECTS:
                self.posts = await api.get_directs()
            else:
                self.posts = []

            container.remove_children()

            if not self.posts:
                container.mount(Static("No posts found", classes="loading"))
            else:
                for post in self.posts:
                    container.mount(PostBlock(post))

        except Exception as e:
            container.remove_children()
            container.mount(
                Static(f"Failed to load: {e}\nPress F5 to retry", classes="error")
            )

    def action_focus_menu(self) -> None:
        """Focus the menu bar."""
        # Focus the first button in the menu bar
        menu = self.query_one(MenuBar)
        first_button = menu.query("Button").first()
        if first_button:
            first_button.focus()

    def action_refresh(self) -> None:
        """Refresh feed."""
        self.run_worker(self.refresh_content())

    def on_menu_bar_view_selected(self, message: MenuBar.ViewSelected) -> None:
        """Handle view change from menu."""
        self.current_view = message.view
        self.run_worker(self.refresh_content())

    def on_menu_bar_back_requested(self, message: MenuBar.BackRequested) -> None:
        """Handle back request."""
        self.notify("Back not yet implemented")
