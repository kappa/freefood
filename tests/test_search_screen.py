"""Tests for SearchScreen behavior."""

from datetime import datetime

import pytest

from freefood.models import Post, User, View
from freefood.screens.search import SearchScreen
from freefood.state import AppState
from freefood.widgets.post import PostBlock


def make_user(
    id: str = "u1",
    username: str = "alice",
    screen_name: str = "Alice",
    user_type: str = "user",
) -> User:
    """Create a test user."""
    return User(id=id, username=username, screen_name=screen_name, type=user_type)


def make_post(
    id: str = "p1",
    body: str = "Test post body",
    author: User | None = None,
) -> Post:
    """Create a test post."""
    now = datetime.now()
    return Post(
        id=id,
        body=body,
        author=author or make_user(),
        groups=[],
        created_at=now,
        updated_at=now,
        comments=[],
        omitted_comments=0,
        omitted_comments_offset=0,
        omitted_comment_likes=0,
        omitted_likes=0,
        likes=[],
    )


class FakeAPI:
    """Minimal API stub for search."""

    def __init__(self, posts: list[Post]) -> None:
        self.posts = posts
        self.calls: list[str] = []

    async def search(self, query: str, offset: int = 0, limit: int = 30) -> list[Post]:
        self.calls.append(query)
        return self.posts


class TestSearchScreen:
    """Tests for SearchScreen."""

    @pytest.mark.asyncio
    async def test_empty_state_when_no_query(self):
        """SearchScreen should show empty state when query is blank."""
        from textual.app import App
        from textual.widgets import Static

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = FakeAPI([])
                self.state = AppState(current_view=View.SEARCH)

            def on_mount(self) -> None:
                self.push_screen(SearchScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, SearchScreen)
            screen.query_one("#search-empty", Static)

    @pytest.mark.asyncio
    async def test_submit_query_calls_api_and_updates_state(self):
        """Submitting a search should call API and show results."""
        from textual.app import App
        from textual.widgets import Input

        posts = [make_post(id="p1", body="Hello world")]
        api = FakeAPI(posts)

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = api
                self.state = AppState(current_view=View.SEARCH)

            def on_mount(self) -> None:
                self.push_screen(SearchScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, SearchScreen)
            search_input = screen.query_one("#search-input", Input)
            search_input.value = "hello"
            search_input.focus()
            await pilot.pause()

            await pilot.press("enter")
            await pilot.pause()

            assert api.calls == ["hello"]
            assert screen.state.search_query == "hello"
            assert screen.query(PostBlock).first() is not None

    @pytest.mark.asyncio
    async def test_escape_clears_query_and_results(self):
        """Escape should clear query and reset results to empty state."""
        from textual.app import App
        from textual.widgets import Input, Static

        posts = [make_post(id="p1", body="Hello world")]
        api = FakeAPI(posts)

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.api = api
                self.state = AppState(current_view=View.SEARCH)

            def on_mount(self) -> None:
                self.push_screen(SearchScreen(self.state))

        async with TestApp().run_test(size=(80, 20)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, SearchScreen)
            search_input = screen.query_one("#search-input", Input)
            search_input.value = "hello"
            search_input.focus()
            await pilot.pause()

            await pilot.press("enter")
            await pilot.pause()

            await pilot.press("escape")
            await pilot.pause()

            assert search_input.value == ""
            screen.query_one("#search-empty", Static)
