"""Screen for displaying a single post."""

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Static

from freefood.models import Post, View
from freefood.screens.base import BaseScreen
from freefood.state import AppState
from freefood.widgets.menu import MenuBar
from freefood.widgets.post import PostBlock


class PostScreen(BaseScreen):
    """Screen for displaying a single post."""

    BINDINGS = [
        ("escape", "focus_menu", "Menu"),
        ("enter", "focus_post", "Post"),
        ("f5", "refresh", "Refresh"),
    ]

    CSS = """
    PostScreen {
        layout: vertical;
    }

    #post-container {
        height: 1fr;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        state: AppState | None = None,
        post: Post | None = None,
        post_id: str | None = None,
    ) -> None:
        super().__init__()
        self._state = state
        self.post = post
        self.post_id = post_id

    @property
    def state(self) -> AppState:
        if self._state is not None:
            return self._state
        return self.app.state

    def compose(self) -> ComposeResult:
        yield MenuBar(self.state.current_view)
        with ScrollableContainer(id="post-container"):
            yield Static("Loading post...", classes="loading")

    async def on_mount(self) -> None:
        await self.refresh_content()

    async def refresh_content(self) -> None:
        container = self.query_one("#post-container")
        container.remove_children()
        container.mount(Static("Loading post...", classes="loading"))

        try:
            if self.post is None:
                if self.post_id is None:
                    raise Exception("Missing post id")
                self.post = await self.api.get_post(self.post_id)

            if self.post is None:
                raise Exception("Post not found")

            container.remove_children()
            container.mount(PostBlock(self.post))
        except Exception as e:
            container.remove_children()
            container.mount(Static(f"Failed to load: {e}", classes="error"))

    def action_focus_menu(self) -> None:
        menu = self.query_one(MenuBar)
        menu.focus_current_view_button()

    def action_focus_post(self) -> None:
        container = self.query_one("#post-container")
        post = container.query(PostBlock).first()
        if post:
            post.focus()

    def action_refresh(self) -> None:
        self.run_worker(self.refresh_content())

    def on_menu_bar_view_selected(self, message: MenuBar.ViewSelected) -> None:
        message.stop()
        self.state.navigate_to(message.view)
        self.push_screen_for_view(message.view)

    def on_menu_bar_back_requested(self, message: MenuBar.BackRequested) -> None:
        message.stop()
        if not self.navigate_back():
            self.notify("No history")
