"""Search screen for querying posts."""

from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import Button, Input, Static

from freefood.models import Post, View
from freefood.screens.base import BaseScreen
from freefood.search import parse_search_terms
from freefood.state import AppState
from freefood.widgets.menu import MenuBar
from freefood.widgets.post import PostBlock


class SearchScreen(BaseScreen):
    """Screen for searching posts."""

    BINDINGS = [
        ("escape", "clear_or_focus_menu", "Clear"),
        ("f5", "refresh", "Refresh"),
    ]

    CSS = """
    SearchScreen {
        layout: vertical;
    }

    #search-bar {
        height: auto;
        padding: 0 1;
    }

    #search-input {
        width: 1fr;
    }

    #search-results {
        height: 1fr;
        padding: 0 1;
    }
    """

    def __init__(self, state: AppState | None = None) -> None:
        super().__init__()
        self._state = state
        self.posts: list[Post] = []

    @property
    def state(self) -> AppState:
        if self._state is not None:
            return self._state
        return self.app.state

    def compose(self) -> ComposeResult:
        yield MenuBar(self.state.current_view)
        with Vertical():
            with Horizontal(id="search-bar"):
                yield Input(placeholder="Search...", id="search-input")
                yield Button("Clear", id="clear-search")
            with ScrollableContainer(id="search-results"):
                yield Static(
                    "Enter a search query", id="search-empty", classes="loading"
                )

    async def on_mount(self) -> None:
        self.state.current_view = View.SEARCH
        search_input = self.query_one("#search-input", Input)
        search_input.value = self.state.search_query
        if self.state.search_query:
            self.run_worker(self.refresh_results())

    async def _show_empty_state(self) -> None:
        container = self.query_one("#search-results", ScrollableContainer)
        await container.remove_children()
        await container.mount(
            Static("Enter a search query", id="search-empty", classes="loading")
        )

    async def _show_loading_state(self) -> None:
        container = self.query_one("#search-results", ScrollableContainer)
        await container.remove_children()
        await container.mount(Static("Searching...", classes="loading"))

    async def refresh_results(self) -> None:
        search_input = self.query_one("#search-input", Input)
        query = search_input.value.strip()
        self.state.search_query = query

        if not query:
            await self._show_empty_state()
            return

        await self._show_loading_state()
        container = self.query_one("#search-results", ScrollableContainer)

        try:
            self.posts = await self.api.search(query)
            await container.remove_children()

            if not self.posts:
                await container.mount(Static("No results found", classes="loading"))
                return

            terms = parse_search_terms(query)
            for post in self.posts:
                await container.mount(PostBlock(post, highlight_terms=terms))
            first_post = container.query(PostBlock).first()
            if first_post:
                first_post.focus()

        except Exception as e:
            await container.remove_children()
            await container.mount(
                Static(f"Search failed: {e}\nPress F5 to retry", classes="error")
            )

    def action_refresh(self) -> None:
        self.run_worker(self.refresh_results())

    def action_clear_or_focus_menu(self) -> None:
        search_input = self.query_one("#search-input", Input)
        if search_input.value:
            search_input.value = ""
            self.state.search_query = ""
            self.run_worker(self._show_empty_state())
        else:
            menu = self.query_one(MenuBar)
            menu.focus_current_view_button()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-input":
            self.run_worker(self.refresh_results())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "clear-search":
            self.action_clear_or_focus_menu()

    def on_menu_bar_view_selected(self, message: MenuBar.ViewSelected) -> None:
        message.stop()
        if message.view == View.SEARCH:
            self.action_refresh()
            return
        self.state.navigate_to(message.view)
        self.push_screen_for_view(message.view)

    def on_menu_bar_back_requested(self, message: MenuBar.BackRequested) -> None:
        message.stop()
        if not self.navigate_back():
            self.notify("No history")
