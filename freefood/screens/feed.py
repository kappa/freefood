"""Feed screen for displaying posts."""

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.screen import Screen
from textual.widgets import Static

from freefood.models import View, Post
from freefood.state import AppState
from freefood.widgets.menu import MenuBar
from freefood.widgets.post import PostBlock


class FeedScreen(Screen):
    """Screen for displaying feed content."""

    BINDINGS = [
        ("escape", "focus_menu", "Menu"),
        ("enter", "focus_feed", "Feed"),
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

    def __init__(self, state: AppState | None = None) -> None:
        """Initialize feed screen."""
        super().__init__()
        self._state = state  # Will use app.state if None
        self.posts: list[Post] = []

    @property
    def state(self) -> AppState:
        """Get app state."""
        if self._state is not None:
            return self._state
        return self.app.state

    def compose(self) -> ComposeResult:
        """Create feed screen widgets."""
        yield MenuBar(self.state.current_view)
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

            if self.state.current_view == View.HOME:
                self.posts = await api.get_home_feed()
            elif self.state.current_view == View.DIRECTS:
                self.posts = await api.get_directs()
            elif self.state.current_view in (View.USER_FEED, View.GROUP_FEED):
                if self.state.current_target:
                    self.posts = await api.get_user_feed(self.state.current_target)
                else:
                    self.posts = []
            else:
                self.posts = []

            container.remove_children()

            if not self.posts:
                container.mount(Static("No posts found", classes="loading"))
            else:
                for post in self.posts:
                    container.mount(PostBlock(post))
                # Focus first post so user can scroll with keyboard
                first_post = container.query(PostBlock).first()
                if first_post:
                    first_post.focus()

        except Exception as e:
            container.remove_children()
            container.mount(
                Static(f"Failed to load: {e}\nPress F5 to retry", classes="error")
            )

    def action_focus_menu(self) -> None:
        """Focus the menu bar."""
        menu = self.query_one(MenuBar)
        menu.focus_current_view_button()

    def action_focus_feed(self) -> None:
        """Focus the feed (first post)."""
        container = self.query_one("#feed-container")
        first_post = container.query(PostBlock).first()
        if first_post:
            first_post.focus()

    def action_refresh(self) -> None:
        """Refresh feed."""
        self.run_worker(self.refresh_content())

    def on_menu_bar_view_selected(self, message: MenuBar.ViewSelected) -> None:
        """Handle view change from menu."""
        if message.view != self.state.current_view:
            self.state.navigate_to(message.view)
            menu = self.query_one(MenuBar)
            menu.set_view(message.view)
        self.run_worker(self.refresh_content())

    def on_menu_bar_back_requested(self, message: MenuBar.BackRequested) -> None:
        """Handle back request."""
        entry = self.state.pop_history()
        if entry:
            self.state.current_view = entry.view
            self.state.current_target = entry.target
            if entry.query:
                self.state.search_query = entry.query
            menu = self.query_one(MenuBar)
            menu.set_view(entry.view)
            self.run_worker(self.refresh_content())
            # TODO: Restore scroll_position after content loads
        else:
            self.notify("No history")

    async def on_post_block_expand_comments(
        self, message: PostBlock.ExpandComments
    ) -> None:
        """Load full comments for a post."""
        try:
            full_post = await self.app.api.get_post(message.post.id)
            if full_post:
                # Find and update the PostBlock
                for block in self.query(PostBlock):
                    if block.post.id == message.post.id:
                        block.post = full_post
                        block.comments_expanded = True
                        block.refresh(recompose=True)
                        break
        except Exception as e:
            self.notify(f"Failed to load comments: {e}", severity="error")

    async def on_post_block_like_requested(
        self, message: PostBlock.LikeRequested
    ) -> None:
        """Handle like/unlike request."""
        post = message.post
        try:
            if post.is_liked:
                await self.app.api.unlike_post(post.id)
                post.is_liked = False
                self.notify("Unliked")
            else:
                await self.app.api.like_post(post.id)
                post.is_liked = True
                self.notify("Liked")
            # Refresh the post block
            for block in self.query(PostBlock):
                if block.post.id == post.id:
                    block.refresh(recompose=True)
                    break
        except Exception as e:
            self.notify(f"Failed: {e}", severity="error")

    async def on_post_block_hide_requested(
        self, message: PostBlock.HideRequested
    ) -> None:
        """Handle hide/unhide request."""
        post = message.post
        try:
            if post.is_hidden:
                await self.app.api.unhide_post(post.id)
                post.is_hidden = False
                self.notify("Unhidden")
            else:
                await self.app.api.hide_post(post.id)
                post.is_hidden = True
                self.notify("Hidden")
            for block in self.query(PostBlock):
                if block.post.id == post.id:
                    block.refresh(recompose=True)
                    break
        except Exception as e:
            self.notify(f"Failed: {e}", severity="error")
