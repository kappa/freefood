# Navigation Refactor Implementation Plan

> **Status:** COMPLETED (2026-02-13)

**Goal:** Unify screen navigation to follow the web browser metaphor — every navigation pushes history, back always pops, re-selecting your own view refreshes content.

**Architecture:** Add `push_screen_for_view(view)` and `navigate_back()` helpers to `BaseScreen`. Replace per-screen navigation dispatch (30-50 lines each in 6 screens) with calls to these helpers. Each screen defines a `action_refresh` for its "re-select self" behavior. Remove FeedScreen's "stay in place for feed views" exception — all view transitions push a new screen.

**Tech Stack:** Python, Textual, pytest-asyncio

---

## Behavior Model (Browser Metaphor)

| Action | Behavior |
|---|---|
| Click **different** menu button | `state.navigate_to(view)` + `push_screen_for_view(view)` |
| Click **same** menu button | `action_refresh()` (screen-specific) |
| Press **Back** | Pop history, restore state, `push_screen_for_view(entry.view)` |
| Back with **no history** | Show "No history" notification |

All screens follow this pattern uniformly. No exceptions.

## Screens affected

- `freefood/screens/base.py` — add helpers
- `freefood/screens/feed.py` — remove stay-in-place exception, use helpers
- `freefood/screens/search.py` — remove custom back-to-search handler, use helpers, keep refresh-on-reselect
- `freefood/screens/notifications.py` — add refresh-on-reselect, use helpers
- `freefood/screens/errors.py` — use helpers (already mostly correct)
- `freefood/screens/theme.py` — use helpers
- `freefood/screens/post.py` — use helpers (no own view, so no reselect)

## Pre-existing test classes that will need updates

These existing tests assert the OLD behavior (FeedScreen stays in place, SearchScreen refreshes in place on back-to-search, etc.) and will need updating:

- `tests/test_feed_screen.py::TestBackNavigation::test_back_to_home_refreshes_feed` — currently asserts FeedScreen stays; should assert FeedScreen pushed
- `tests/test_feed_screen.py::TestFeedScreenMenuNavigation` — only has one test; needs tests for feed-to-feed navigation pushing new screen
- `tests/test_search_screen.py::TestSearchBackNavigation::test_back_to_search_refreshes` — asserts SearchScreen stays; should assert SearchScreen pushed
- `tests/test_notifications_screen.py::TestNotificationsMenuNavigation::test_selecting_notifications_is_noop` — should assert refresh instead of noop

---

### ~~Task 1: Add `push_screen_for_view` and `navigate_back` to BaseScreen~~ DONE

**Files:**
- Modify: `freefood/screens/base.py`
- Test: `tests/test_base_screen.py` (create)

**Step 1: Write failing tests for BaseScreen helpers**

Create `tests/test_base_screen.py`:

```python
"""Tests for BaseScreen navigation helpers."""

import pytest
from textual.app import App

from freefood.models import HistoryEntry, View
from freefood.screens.base import BaseScreen
from freefood.state import AppState
from freefood.widgets.menu import MenuBar


class MinimalScreen(BaseScreen):
    """Minimal screen for testing BaseScreen helpers."""

    def compose(self):
        yield MenuBar(View.HOME)


class MockApp(App):
    def __init__(self, state=None):
        super().__init__()
        self.state = state or AppState()
        self.pushed_screens = []
        self._original_push = None

    async def on_mount(self):
        self._original_push = self.push_screen

        def tracking_push(screen, *args, **kwargs):
            self.pushed_screens.append(screen)
            return self._original_push(screen, *args, **kwargs)

        self.push_screen = tracking_push


class TestPushScreenForView:
    """Tests for push_screen_for_view helper."""

    @pytest.mark.asyncio
    async def test_push_feed_screen_for_home(self):
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.push_screen_for_view(View.HOME)
            await pilot.pause()
            from freefood.screens.feed import FeedScreen
            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_push_search_screen(self):
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.push_screen_for_view(View.SEARCH)
            await pilot.pause()
            from freefood.screens.search import SearchScreen
            assert any(isinstance(s, SearchScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_push_notifications_screen(self):
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.push_screen_for_view(View.NOTIFICATIONS)
            await pilot.pause()
            from freefood.screens.notifications import NotificationsScreen
            assert any(isinstance(s, NotificationsScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_push_errors_screen(self):
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.push_screen_for_view(View.ERRORS)
            await pilot.pause()
            from freefood.screens.errors import ErrorsScreen
            assert any(isinstance(s, ErrorsScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_push_theme_screen(self):
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.push_screen_for_view(View.THEME)
            await pilot.pause()
            from freefood.screens.theme import ThemeScreen
            assert any(isinstance(s, ThemeScreen) for s in app.pushed_screens)

    @pytest.mark.asyncio
    async def test_push_feed_screen_for_directs(self):
        app = MockApp()
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.push_screen_for_view(View.DIRECTS)
            await pilot.pause()
            from freefood.screens.feed import FeedScreen
            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)


class TestNavigateBack:
    """Tests for navigate_back helper."""

    @pytest.mark.asyncio
    async def test_navigate_back_pops_and_pushes(self):
        state = AppState()
        state.history.append(
            HistoryEntry(view=View.HOME, target=None, scroll_position=0)
        )
        app = MockApp(state=state)
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            result = screen.navigate_back()
            assert result is True
            await pilot.pause()
            from freefood.screens.feed import FeedScreen
            assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)
            assert state.current_view == View.HOME

    @pytest.mark.asyncio
    async def test_navigate_back_restores_search_query(self):
        state = AppState()
        state.history.append(
            HistoryEntry(view=View.SEARCH, target=None, scroll_position=0, query="test")
        )
        app = MockApp(state=state)
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.navigate_back()
            await pilot.pause()
            assert state.search_query == "test"

    @pytest.mark.asyncio
    async def test_navigate_back_restores_target(self):
        state = AppState()
        state.history.append(
            HistoryEntry(view=View.USER_FEED, target="bob", scroll_position=0)
        )
        app = MockApp(state=state)
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.navigate_back()
            await pilot.pause()
            assert state.current_target == "bob"

    @pytest.mark.asyncio
    async def test_navigate_back_empty_history_returns_false(self):
        state = AppState()
        app = MockApp(state=state)
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            result = screen.navigate_back()
            assert result is False

    @pytest.mark.asyncio
    async def test_navigate_back_does_not_overwrite_query_when_none(self):
        state = AppState(search_query="existing")
        state.history.append(
            HistoryEntry(view=View.HOME, target=None, scroll_position=0)
        )
        app = MockApp(state=state)
        async with app.run_test() as pilot:
            await app.push_screen(MinimalScreen())
            await pilot.pause()
            screen = app.screen
            screen.navigate_back()
            await pilot.pause()
            assert state.search_query == "existing"
```

**Step 2: Run tests to verify they fail**

Run: `/home/kappa/work/frf/freefood/.venv/bin/pytest tests/test_base_screen.py -v`
Expected: FAIL — `push_screen_for_view` and `navigate_back` don't exist on BaseScreen yet.

**Step 3: Implement BaseScreen helpers**

Add to `freefood/screens/base.py`:

```python
def push_screen_for_view(self, view: View) -> None:
    """Push the appropriate screen for a given view."""
    from freefood.screens.errors import ErrorsScreen
    from freefood.screens.feed import FeedScreen
    from freefood.screens.notifications import NotificationsScreen
    from freefood.screens.search import SearchScreen
    from freefood.screens.theme import ThemeScreen

    state = self.app.state
    screen_map: dict[View, Screen] = {
        View.SEARCH: SearchScreen(state),
        View.NOTIFICATIONS: NotificationsScreen(state),
        View.ERRORS: ErrorsScreen(),
        View.THEME: ThemeScreen(),
    }
    self.app.push_screen(screen_map.get(view, FeedScreen(state)))

def navigate_back(self) -> bool:
    """Pop history, restore state, push screen. Returns False if no history."""
    entry = self.app.state.pop_history()
    if not entry:
        return False
    self.app.state.current_view = entry.view
    self.app.state.current_target = entry.target
    if entry.query is not None:
        self.app.state.search_query = entry.query
    self.push_screen_for_view(entry.view)
    return True
```

**Step 4: Run tests to verify they pass**

Run: `/home/kappa/work/frf/freefood/.venv/bin/pytest tests/test_base_screen.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add freefood/screens/base.py tests/test_base_screen.py
git commit -m "feat: add push_screen_for_view and navigate_back to BaseScreen"
```

---

### ~~Task 2: Update FeedScreen navigation tests, then refactor FeedScreen~~ DONE

**Files:**
- Modify: `freefood/screens/feed.py:319-374`
- Modify: `tests/test_feed_screen.py` — TestFeedScreenMenuNavigation, TestBackNavigation

**Step 1: Update existing FeedScreen navigation tests for new behavior**

The key behavioral change: FeedScreen no longer stays in place when navigating to another feed view. It pushes a new screen like everyone else. It also refreshes on re-select.

Update `test_back_to_home_refreshes_feed` — rename and change assertion: should push FeedScreen, not stay in place.

Add new tests:
- `test_selecting_own_view_refreshes` — clicking HOME when on HOME refreshes
- `test_selecting_directs_pushes_feed_screen` — clicking DIRECTS from HOME pushes new FeedScreen
- `test_back_to_feed_view_pushes_feed_screen` — back to HOME pushes new FeedScreen (not stays)

**Step 2: Run tests to verify they fail (RED)**

The new/updated tests will fail because FeedScreen still has the old stay-in-place behavior.

**Step 3: Refactor FeedScreen navigation handlers**

Replace `on_menu_bar_view_selected` (~35 lines) with:

```python
def on_menu_bar_view_selected(self, message: MenuBar.ViewSelected) -> None:
    message.stop()
    if message.view == self.state.current_view:
        self.action_refresh()
        return
    self.state.navigate_to(message.view)
    self.push_screen_for_view(message.view)
```

Replace `on_menu_bar_back_requested` (~18 lines) with:

```python
def on_menu_bar_back_requested(self, message: MenuBar.BackRequested) -> None:
    message.stop()
    if not self.navigate_back():
        self.notify("No history")
```

**Step 4: Run tests to verify they pass (GREEN)**

Run: `/home/kappa/work/frf/freefood/.venv/bin/pytest tests/test_feed_screen.py -v`

**Step 5: Commit**

```bash
git commit -m "refactor: FeedScreen uses BaseScreen navigation helpers"
```

---

### ~~Task 3: Update NotificationsScreen — add refresh-on-reselect, use helpers~~ DONE

**Files:**
- Modify: `freefood/screens/notifications.py:111-159`
- Modify: `tests/test_notifications_screen.py` — update noop test to expect refresh

**Step 1: Update tests**

Change `test_selecting_notifications_is_noop` to `test_selecting_notifications_refreshes` — assert `action_refresh` is called.

**Step 2: Verify RED**

**Step 3: Refactor NotificationsScreen**

```python
def on_menu_bar_view_selected(self, message: MenuBar.ViewSelected) -> None:
    message.stop()
    if message.view == View.NOTIFICATIONS:
        self.action_refresh()
        return
    self.state.navigate_to(message.view)
    self.push_screen_for_view(message.view)

def on_menu_bar_back_requested(self, message: MenuBar.BackRequested) -> None:
    message.stop()
    if not self.navigate_back():
        self.notify("No history")
```

**Step 4: Verify GREEN**

**Step 5: Commit**

---

### ~~Task 4: Update SearchScreen — use helpers, keep refresh-on-reselect~~ DONE

**Files:**
- Modify: `freefood/screens/search.py:138-187`
- Modify: `tests/test_search_screen.py` — update back-to-search test

**Step 1: Update tests**

Change `test_back_to_search_refreshes` — should assert SearchScreen is pushed (not refreshed in place).

**Step 2: Verify RED**

**Step 3: Refactor SearchScreen**

```python
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
```

Also remove `_return_to_feed` method — it's no longer needed.

**Step 4: Verify GREEN**

**Step 5: Commit**

---

### ~~Task 5: Refactor ErrorsScreen — use helpers~~ DONE

**Files:**
- Modify: `freefood/screens/errors.py:102-149`
- Test: existing tests in `tests/test_errors_screen.py` should still pass unchanged

**Step 1: Run existing ErrorsScreen tests to verify GREEN baseline**

**Step 2: Refactor ErrorsScreen**

```python
def on_menu_bar_view_selected(self, message: MenuBar.ViewSelected) -> None:
    message.stop()
    if message.view == View.ERRORS:
        self.action_refresh()
        return
    self.app.state.navigate_to(message.view)
    self.push_screen_for_view(message.view)

def on_menu_bar_back_requested(self, message: MenuBar.BackRequested) -> None:
    message.stop()
    if not self.navigate_back():
        self.notify("No history")
```

**Step 3: Run tests to verify GREEN**

**Step 4: Commit**

---

### ~~Task 6: Refactor ThemeScreen — use helpers~~ DONE

**Files:**
- Modify: `freefood/screens/theme.py:77-127`
- Test: existing tests in `tests/test_theme_screen.py` should still pass

**Step 1: Run existing ThemeScreen tests to verify GREEN baseline**

**Step 2: Refactor ThemeScreen**

```python
def on_menu_bar_view_selected(self, message: MenuBar.ViewSelected) -> None:
    message.stop()
    if message.view == View.THEME:
        return  # theme screen is static, nothing to refresh
    self.app.state.navigate_to(message.view)
    self.push_screen_for_view(message.view)

def on_menu_bar_back_requested(self, message: MenuBar.BackRequested) -> None:
    message.stop()
    if not self.navigate_back():
        self.notify("No history")
```

**Step 3: Run tests to verify GREEN**

**Step 4: Commit**

---

### ~~Task 7: Refactor PostScreen — use helpers~~ DONE

**Files:**
- Modify: `freefood/screens/post.py:92-136`
- Test: existing tests in `tests/test_post_screen.py` should still pass

PostScreen has no "own view" in the menu, so no refresh behavior. It always navigates away.

**Step 1: Run existing PostScreen tests to verify GREEN baseline**

**Step 2: Refactor PostScreen**

```python
def on_menu_bar_view_selected(self, message: MenuBar.ViewSelected) -> None:
    message.stop()
    self.state.navigate_to(message.view)
    self.push_screen_for_view(message.view)

def on_menu_bar_back_requested(self, message: MenuBar.BackRequested) -> None:
    message.stop()
    if not self.navigate_back():
        self.notify("No history")
```

**Step 3: Run tests to verify GREEN**

**Step 4: Commit**

---

### ~~Task 8: Full quality gate + final commit~~ DONE

**Step 1: Run all checks**

```bash
/home/kappa/work/frf/freefood/.venv/bin/ruff check freefood/ tests/
/home/kappa/work/frf/freefood/.venv/bin/ruff format --check freefood/ tests/
/home/kappa/work/frf/freefood/.venv/bin/mypy freefood/
/home/kappa/work/frf/freefood/.venv/bin/pytest tests/ -v
```

All must pass with coverage >= 95%.

**Step 2: Squash or clean up commits if needed**
