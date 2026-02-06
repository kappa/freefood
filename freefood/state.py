"""Application state management."""

from dataclasses import dataclass, field

from freefood.models import HistoryEntry, View

MAX_HISTORY_SIZE = 50


@dataclass
class AppState:
    """Global application state."""

    current_view: View = View.HOME
    current_target: str | None = None  # username for USER_FEED/GROUP_FEED
    search_query: str = ""
    history: list[HistoryEntry] = field(default_factory=list)

    def push_history(self, scroll_position: int = 0) -> None:
        """Push current state to history before navigation."""
        entry = HistoryEntry(
            view=self.current_view,
            target=self.current_target,
            scroll_position=scroll_position,
            query=self.search_query if self.current_view == View.SEARCH else None,
        )
        self.history.append(entry)
        # Trim history to max size
        if len(self.history) > MAX_HISTORY_SIZE:
            self.history = self.history[-MAX_HISTORY_SIZE:]

    def pop_history(self) -> HistoryEntry | None:
        """Pop and return previous state, or None if empty."""
        if self.history:
            return self.history.pop()
        return None

    def can_go_back(self) -> bool:
        """Check if back navigation is possible."""
        return len(self.history) > 0

    def navigate_to(
        self, view: View, target: str | None = None, scroll_position: int = 0
    ) -> None:
        """Navigate to a new view, pushing current to history."""
        self.push_history(scroll_position)
        self.current_view = view
        self.current_target = target
