"""Tests for application state management."""

from freefood.models import View, HistoryEntry
from freefood.state import AppState, MAX_HISTORY_SIZE


def test_appstate_default_initialization():
    """AppState should initialize with correct default values."""
    state = AppState()
    assert state.current_view == View.HOME
    assert state.current_target is None
    assert state.search_query == ""
    assert state.history == []


def test_appstate_custom_initialization():
    """AppState can be initialized with custom values."""
    state = AppState(
        current_view=View.USER_FEED,
        current_target="alice",
        search_query="test",
    )
    assert state.current_view == View.USER_FEED
    assert state.current_target == "alice"
    assert state.search_query == "test"


def test_push_history_adds_entry():
    """push_history() should add current state to history."""
    state = AppState(current_view=View.HOME)
    state.push_history(scroll_position=100)

    assert len(state.history) == 1
    entry = state.history[0]
    assert entry.view == View.HOME
    assert entry.target is None
    assert entry.scroll_position == 100
    assert entry.query is None


def test_push_history_preserves_target():
    """push_history() should preserve current_target in entry."""
    state = AppState(current_view=View.USER_FEED, current_target="bob")
    state.push_history()

    assert len(state.history) == 1
    assert state.history[0].target == "bob"


def test_push_history_stores_query_for_search_view():
    """push_history() should store search_query when in SEARCH view."""
    state = AppState(
        current_view=View.SEARCH,
        search_query="python textual",
    )
    state.push_history()

    assert len(state.history) == 1
    assert state.history[0].query == "python textual"


def test_push_history_does_not_store_query_for_non_search_view():
    """push_history() should not store query when not in SEARCH view."""
    state = AppState(
        current_view=View.HOME,
        search_query="leftover query",
    )
    state.push_history()

    assert len(state.history) == 1
    assert state.history[0].query is None


def test_push_history_multiple_entries():
    """push_history() should add multiple entries correctly."""
    state = AppState(current_view=View.HOME)
    state.push_history(scroll_position=0)

    state.current_view = View.NOTIFICATIONS
    state.push_history(scroll_position=50)

    state.current_view = View.USER_FEED
    state.current_target = "alice"
    state.push_history(scroll_position=100)

    assert len(state.history) == 3
    assert state.history[0].view == View.HOME
    assert state.history[1].view == View.NOTIFICATIONS
    assert state.history[2].view == View.USER_FEED
    assert state.history[2].target == "alice"


def test_push_history_trims_to_max_size():
    """push_history() should trim history to MAX_HISTORY_SIZE."""
    state = AppState()

    # Push more than MAX_HISTORY_SIZE entries
    for i in range(MAX_HISTORY_SIZE + 10):
        state.current_view = View.HOME if i % 2 == 0 else View.NOTIFICATIONS
        state.push_history(scroll_position=i)

    assert len(state.history) == MAX_HISTORY_SIZE


def test_push_history_keeps_most_recent_when_trimming():
    """push_history() should keep most recent entries when trimming."""
    state = AppState()

    # Push entries with distinguishable scroll positions
    for i in range(MAX_HISTORY_SIZE + 10):
        state.push_history(scroll_position=i)

    # The oldest entries (0-9) should be gone, keeping 10 through 59
    assert state.history[0].scroll_position == 10
    assert state.history[-1].scroll_position == MAX_HISTORY_SIZE + 9


def test_pop_history_returns_last_entry():
    """pop_history() should return and remove the last entry."""
    state = AppState()
    state.current_view = View.HOME
    state.push_history(scroll_position=10)

    state.current_view = View.NOTIFICATIONS
    state.push_history(scroll_position=20)

    entry = state.pop_history()

    assert entry is not None
    assert entry.view == View.NOTIFICATIONS
    assert entry.scroll_position == 20
    assert len(state.history) == 1


def test_pop_history_returns_none_when_empty():
    """pop_history() should return None when history is empty."""
    state = AppState()
    result = state.pop_history()
    assert result is None


def test_pop_history_empties_history():
    """pop_history() should eventually empty the history."""
    state = AppState()
    state.push_history()
    state.push_history()

    state.pop_history()
    state.pop_history()
    result = state.pop_history()

    assert result is None
    assert len(state.history) == 0


def test_can_go_back_returns_false_when_empty():
    """can_go_back() should return False when history is empty."""
    state = AppState()
    assert state.can_go_back() is False


def test_can_go_back_returns_true_with_history():
    """can_go_back() should return True when history has entries."""
    state = AppState()
    state.push_history()
    assert state.can_go_back() is True


def test_can_go_back_updates_after_pop():
    """can_go_back() should update correctly after pop_history()."""
    state = AppState()
    state.push_history()

    assert state.can_go_back() is True
    state.pop_history()
    assert state.can_go_back() is False


def test_navigate_to_pushes_current_state():
    """navigate_to() should push current state to history."""
    state = AppState(current_view=View.HOME)
    state.navigate_to(View.NOTIFICATIONS)

    assert len(state.history) == 1
    assert state.history[0].view == View.HOME


def test_navigate_to_updates_current_view():
    """navigate_to() should update current_view to new view."""
    state = AppState(current_view=View.HOME)
    state.navigate_to(View.USER_FEED, target="alice")

    assert state.current_view == View.USER_FEED


def test_navigate_to_updates_target():
    """navigate_to() should update current_target."""
    state = AppState(current_view=View.HOME, current_target=None)
    state.navigate_to(View.USER_FEED, target="bob")

    assert state.current_target == "bob"


def test_navigate_to_clears_target_when_none():
    """navigate_to() should clear target when navigating to view without target."""
    state = AppState(current_view=View.USER_FEED, current_target="alice")
    state.navigate_to(View.HOME)

    assert state.current_target is None


def test_navigate_to_preserves_scroll_position():
    """navigate_to() should preserve scroll position in history entry."""
    state = AppState(current_view=View.HOME)
    state.navigate_to(View.NOTIFICATIONS, scroll_position=250)

    assert state.history[0].scroll_position == 250


def test_navigate_to_chain():
    """navigate_to() should work correctly for navigation chain."""
    state = AppState()

    state.navigate_to(View.NOTIFICATIONS)
    state.navigate_to(View.USER_FEED, target="alice")
    state.navigate_to(View.SEARCH)

    assert len(state.history) == 3
    assert state.current_view == View.SEARCH
    assert state.history[0].view == View.HOME
    assert state.history[1].view == View.NOTIFICATIONS
    assert state.history[2].view == View.USER_FEED
    assert state.history[2].target == "alice"


def test_max_history_size_constant():
    """MAX_HISTORY_SIZE should be 50."""
    assert MAX_HISTORY_SIZE == 50
