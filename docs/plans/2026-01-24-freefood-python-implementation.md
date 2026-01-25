# FreeFood Console Client - Python Reference Implementation

Version: 1.0
Date: 2026-01-24

This document describes the reference implementation using Python and Textual. For the language-independent design, see `2026-01-24-freefood-design.md`.

## Technology Choices

### Language: Python 3.11+

- Concise, readable code
- Excellent library ecosystem
- Cross-platform by default

### Libraries

| Purpose | Library | Version | Notes |
|---------|---------|---------|-------|
| TUI framework | `textual` | ≥0.47 | Modern async TUI, cross-platform |
| HTTP client | `httpx` | ≥0.27 | Async support, clean API |
| Config paths | `platformdirs` | ≥4.0 | XDG-compliant paths on all platforms |
| Config parsing | `configparser` | stdlib | INI file support |
| Browser launch | `webbrowser` | stdlib | Open auth URL |
| Data classes | `dataclasses` | stdlib | Model definitions |

### Why Textual?

- Modern, actively maintained (by Textualize)
- Async-first design
- Rich widget library
- CSS-like styling
- Works on Linux, macOS, Windows
- Mouse support (optional, but available)
- Good documentation

---

## Project Structure

```
freefood/
├── freefood/
│   ├── __init__.py          # Package metadata, version
│   ├── __main__.py          # Entry point (python -m freefood)
│   ├── app.py               # Main Textual Application class
│   ├── api.py               # FreeFeed API client
│   ├── config.py            # Config file handling
│   ├── models.py            # Dataclasses: Post, Comment, User, etc.
│   ├── state.py             # Application state management
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── post.py          # PostBlock widget
│   │   ├── comment.py       # Comment widget
│   │   ├── compose.py       # ComposeBlock widget
│   │   ├── editor.py        # InlineEditor widget
│   │   ├── menu.py          # MenuBar widget
│   │   └── notification.py  # NotificationBlock widget
│   └── screens/
│       ├── __init__.py
│       ├── feed.py          # FeedScreen (Home, User, Group, Search, Directs)
│       ├── notifications.py # NotificationsScreen
│       └── auth.py          # AuthScreen (first-run)
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_models.py
│   └── test_widgets.py
├── pyproject.toml           # Project metadata, dependencies
└── README.md                # User documentation
```

---

## Module Specifications

### `models.py`

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    id: str
    username: str
    screen_name: str
    type: str  # "user" or "group"
    profile_picture_url: str | None = None

@dataclass
class Comment:
    id: str
    body: str
    author: User
    created_at: datetime
    likes: int
    is_liked: bool = False
    is_own: bool = False

@dataclass
class Post:
    id: str
    body: str
    author: User
    groups: list[User]
    created_at: datetime
    updated_at: datetime
    comments: list[Comment]
    omitted_comments: int
    omitted_likes: int
    likes: list[User]
    is_liked: bool = False
    is_hidden: bool = False
    is_own: bool = False

@dataclass
class Notification:
    id: str
    type: str  # "comment", "mention", "subscription", etc.
    actor: User
    target_post: Post | None
    target_comment: Comment | None
    created_at: datetime

class View(Enum):
    HOME = "home"
    NOTIFICATIONS = "notifications"
    DIRECTS = "directs"
    SEARCH = "search"
    USER_FEED = "user_feed"
    GROUP_FEED = "group_feed"

@dataclass
class HistoryEntry:
    view: View
    target: str | None  # username/group for USER_FEED/GROUP_FEED
    scroll_position: int
    query: str | None  # for SEARCH
```

### `api.py`

```python
import httpx
from .models import Post, Comment, User, Notification

class FreeFeedAPI:
    BASE_URL = "https://freefeed.net"

    def __init__(self, token: str):
        self.token = token
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0
        )
        self.current_user: User | None = None

    async def validate_token(self) -> User:
        """Validate token and return current user."""
        response = await self.client.get("/v2/users/whoami")
        response.raise_for_status()
        data = response.json()
        self.current_user = self._parse_user(data["users"])
        return self.current_user

    async def get_home_feed(self, offset: int = 0, limit: int = 30) -> list[Post]:
        """Fetch home timeline."""
        response = await self.client.get(
            "/v2/timelines/home",
            params={"offset": offset, "limit": limit}
        )
        response.raise_for_status()
        return self._denormalize_posts(response.json())

    async def get_user_feed(self, username: str, offset: int = 0, limit: int = 30) -> list[Post]:
        """Fetch user timeline."""
        response = await self.client.get(
            f"/v2/timelines/{username}",
            params={"offset": offset, "limit": limit}
        )
        response.raise_for_status()
        return self._denormalize_posts(response.json())

    async def get_notifications(self, offset: int = 0, limit: int = 30) -> list[Notification]:
        """Fetch notifications."""
        response = await self.client.get(
            "/v2/notifications",
            params={"offset": offset, "limit": limit}
        )
        response.raise_for_status()
        return self._parse_notifications(response.json())

    async def get_directs(self, offset: int = 0, limit: int = 30) -> list[Post]:
        """Fetch direct messages."""
        response = await self.client.get(
            "/v2/timelines/filter/directs",
            params={"offset": offset, "limit": limit}
        )
        response.raise_for_status()
        return self._denormalize_posts(response.json())

    async def search(self, query: str, offset: int = 0, limit: int = 30) -> list[Post]:
        """Search posts."""
        response = await self.client.get(
            "/v2/search",
            params={"q": query, "offset": offset, "limit": limit}
        )
        response.raise_for_status()
        return self._denormalize_posts(response.json())

    async def get_post(self, post_id: str) -> Post:
        """Fetch single post with all comments."""
        response = await self.client.get(
            f"/v2/posts/{post_id}",
            params={"maxComments": "all", "maxLikes": "all"}
        )
        response.raise_for_status()
        posts = self._denormalize_posts(response.json())
        return posts[0] if posts else None

    async def create_post(self, body: str, feeds: list[str]) -> Post:
        """Create a new post."""
        response = await self.client.post(
            "/v2/posts",
            json={"post": {"body": body}, "meta": {"feeds": feeds}}
        )
        response.raise_for_status()
        posts = self._denormalize_posts(response.json())
        return posts[0]

    async def update_post(self, post_id: str, body: str) -> Post:
        """Update a post."""
        response = await self.client.put(
            f"/v2/posts/{post_id}",
            json={"post": {"body": body}}
        )
        response.raise_for_status()
        posts = self._denormalize_posts(response.json())
        return posts[0]

    async def delete_post(self, post_id: str) -> None:
        """Delete a post."""
        response = await self.client.delete(f"/v2/posts/{post_id}")
        response.raise_for_status()

    async def like_post(self, post_id: str) -> None:
        response = await self.client.post(f"/v2/posts/{post_id}/like")
        response.raise_for_status()

    async def unlike_post(self, post_id: str) -> None:
        response = await self.client.post(f"/v2/posts/{post_id}/unlike")
        response.raise_for_status()

    async def hide_post(self, post_id: str) -> None:
        response = await self.client.post(f"/v2/posts/{post_id}/hide")
        response.raise_for_status()

    async def unhide_post(self, post_id: str) -> None:
        response = await self.client.post(f"/v2/posts/{post_id}/unhide")
        response.raise_for_status()

    async def create_comment(self, post_id: str, body: str) -> Comment:
        """Create a comment on a post."""
        response = await self.client.post(
            "/v2/comments",
            json={"comment": {"body": body, "postId": post_id}}
        )
        response.raise_for_status()
        return self._parse_comment(response.json())

    async def update_comment(self, comment_id: str, body: str) -> Comment:
        response = await self.client.put(
            f"/v2/comments/{comment_id}",
            json={"comment": {"body": body}}
        )
        response.raise_for_status()
        return self._parse_comment(response.json())

    async def delete_comment(self, comment_id: str) -> None:
        response = await self.client.delete(f"/v2/comments/{comment_id}")
        response.raise_for_status()

    async def like_comment(self, comment_id: str) -> None:
        response = await self.client.post(f"/v2/comments/{comment_id}/like")
        response.raise_for_status()

    async def unlike_comment(self, comment_id: str) -> None:
        response = await self.client.post(f"/v2/comments/{comment_id}/unlike")
        response.raise_for_status()

    async def subscribe(self, username: str) -> None:
        response = await self.client.post(f"/v2/users/{username}/subscribe")
        response.raise_for_status()

    async def unsubscribe(self, username: str) -> None:
        response = await self.client.post(f"/v2/users/{username}/unsubscribe")
        response.raise_for_status()

    def _denormalize_posts(self, data: dict) -> list[Post]:
        """Convert normalized API response to Post objects."""
        users_by_id = {u["id"]: self._parse_user(u) for u in data.get("users", [])}
        comments_by_id = {}
        for c in data.get("comments", []):
            comments_by_id[c["id"]] = self._parse_comment_raw(c, users_by_id)

        posts = []
        for p in data.get("posts", []):
            posts.append(self._parse_post(p, users_by_id, comments_by_id))
        return posts

    def _parse_user(self, data: dict) -> User:
        return User(
            id=data["id"],
            username=data["username"],
            screen_name=data.get("screenName", data["username"]),
            type=data.get("type", "user"),
            profile_picture_url=data.get("profilePictureMediumUrl")
        )

    def _parse_post(self, data: dict, users: dict, comments: dict) -> Post:
        author = users.get(data["createdBy"])
        post_comments = [comments[cid] for cid in data.get("comments", []) if cid in comments]
        post_likes = [users[uid] for uid in data.get("likes", []) if uid in users]
        groups = [users[fid] for fid in data.get("postedTo", []) if fid in users and users[fid].type == "group"]

        return Post(
            id=data["id"],
            body=data["body"],
            author=author,
            groups=groups,
            created_at=datetime.fromtimestamp(int(data["createdAt"]) / 1000),
            updated_at=datetime.fromtimestamp(int(data["updatedAt"]) / 1000),
            comments=post_comments,
            omitted_comments=data.get("omittedComments", 0),
            omitted_likes=data.get("omittedLikes", 0),
            likes=post_likes,
            is_liked=data.get("isLiked", False),
            is_hidden=data.get("isHidden", False),
            is_own=(author and self.current_user and author.id == self.current_user.id)
        )

    # ... additional parsing methods
```

### `config.py`

```python
import configparser
from pathlib import Path
from platformdirs import user_config_dir

APP_NAME = "freefood"
AUTH_URL = (
    "https://freefeed.net/settings/app-tokens/create"
    "?title=FreeFood%20(Console%20Client)"
    "&scopes=read-my-info%20read-my-files%20read-feeds%20read-users-info"
    "%20read-realtime%20manage-my-files%20manage-notifications%20manage-posts"
    "%20manage-my-feeds%20manage-profile%20manage-groups%20manage-subscription-requests"
)

def get_config_path() -> Path:
    """Get platform-appropriate config file path."""
    config_dir = Path(user_config_dir(APP_NAME))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.ini"

def load_config() -> configparser.ConfigParser:
    """Load config from file."""
    config = configparser.ConfigParser()
    config_path = get_config_path()
    if config_path.exists():
        config.read(config_path)
    return config

def save_config(config: configparser.ConfigParser) -> None:
    """Save config to file."""
    config_path = get_config_path()
    with open(config_path, "w") as f:
        config.write(f)

def get_token() -> str | None:
    """Get stored auth token."""
    config = load_config()
    return config.get("auth", "token", fallback=None)

def save_token(token: str, username: str) -> None:
    """Save auth token and username."""
    config = load_config()
    if "auth" not in config:
        config["auth"] = {}
    if "user" not in config:
        config["user"] = {}
    config["auth"]["token"] = token
    config["user"]["username"] = username
    save_config(config)
```

### `app.py`

```python
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen

from .api import FreeFeedAPI
from .config import get_token, AUTH_URL
from .state import AppState
from .screens.feed import FeedScreen
from .screens.notifications import NotificationsScreen
from .screens.auth import AuthScreen

class FreeFoodApp(App):
    """FreeFeed console client."""

    TITLE = "FreeFood"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("f5", "refresh", "Refresh"),
        Binding("escape", "back_or_menu", "Back/Menu"),
    ]

    def __init__(self):
        super().__init__()
        self.api: FreeFeedAPI | None = None
        self.state = AppState()

    async def on_mount(self) -> None:
        """Initialize app on startup."""
        token = get_token()
        if token:
            self.api = FreeFeedAPI(token)
            try:
                await self.api.validate_token()
                self.push_screen(FeedScreen())
            except Exception:
                self.push_screen(AuthScreen())
        else:
            self.push_screen(AuthScreen())

    async def action_refresh(self) -> None:
        """Refresh current view."""
        screen = self.screen
        if hasattr(screen, "refresh_content"):
            await screen.refresh_content()

    def action_back_or_menu(self) -> None:
        """Go back or focus menu."""
        screen = self.screen
        if hasattr(screen, "handle_escape"):
            screen.handle_escape()
```

---

## Widget Specifications

### `widgets/post.py` - PostBlock

A Textual widget displaying a single post with all its elements.

Key responsibilities:
- Render post header, body, action bar, likes, comments
- Handle focus cycling through interactive elements
- Emit events for actions (like, comment, edit, delete, navigate)
- Manage truncation state (collapsed/expanded)

### `widgets/compose.py` - ComposeBlock

Widget for creating new posts.

Key responsibilities:
- Collapsed state (placeholder text)
- Expanded state (text area, groups input, buttons)
- Emit post creation events

### `widgets/editor.py` - InlineEditor

Reusable editor for comments and post editing.

Key responsibilities:
- Multi-line text input
- Tab navigation between text, cancel, submit
- Keyboard shortcuts (Ctrl+Enter, Escape)
- Emit submit/cancel events

### `widgets/menu.py` - MenuBar

Top navigation bar.

Key responsibilities:
- Render menu items with selection highlight
- Handle left/right/tab navigation
- Emit navigation events (change view, go back)

---

## Styling (`app.tcss`)

Textual uses CSS-like syntax for styling:

```css
/* Menu bar */
MenuBar {
    dock: top;
    height: 1;
    background: $primary;
}

MenuBar .selected {
    background: $secondary;
    text-style: bold;
}

/* Post block */
PostBlock {
    border: solid $primary;
    margin: 1 0;
    padding: 1;
}

PostBlock.selected {
    border: solid $accent;
}

/* Comments */
Comment {
    padding-left: 2;
}

Comment .likes {
    color: $error;
}

/* Editor */
InlineEditor {
    border: dashed $secondary;
    padding: 1;
}

/* Loading/Error states */
.loading {
    text-align: center;
    color: $text-muted;
}

.error {
    text-align: center;
    color: $error;
}
```

---

## Entry Point (`__main__.py`)

```python
from .app import FreeFoodApp

def main():
    app = FreeFoodApp()
    app.run()

if __name__ == "__main__":
    main()
```

---

## Package Configuration (`pyproject.toml`)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "freefood"
version = "1.0.0"
description = "Console client for FreeFeed.net"
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
authors = [
    { name = "Alex Kapranoff", email = "kapranoff@gmail.com" }
]
keywords = ["freefeed", "social", "tui", "console", "terminal"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Communications",
]
dependencies = [
    "textual>=0.47",
    "httpx>=0.27",
    "platformdirs>=4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.0",
]

[project.scripts]
freefood = "freefood.__main__:main"

[project.urls]
Homepage = "https://github.com/kappa/freefood"
Repository = "https://github.com/kappa/freefood"

[tool.hatch.build.targets.wheel]
packages = ["freefood"]
```

---

## Testing Strategy

### Unit Tests

- `test_models.py`: Data class creation, edge cases
- `test_api.py`: Mock HTTP responses, denormalization logic
- `test_config.py`: Config loading/saving

### Integration Tests

- Test full API calls against a test server (if available)
- Test widget rendering and interaction

### Manual Testing

- Test on Linux, macOS, Windows
- Test various terminal emulators
- Test keyboard navigation flows

---

## Development Workflow

```bash
# Clone and setup
git clone <repo>
cd freefood
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"

# Run
freefood
# or
python -m freefood

# Test
pytest

# Build
pip install build
python -m build
```

---

## Implementation Order

Suggested order for incremental development:

1. **Config & Auth** - config.py, auth screen, token validation
2. **API Client** - api.py with home feed endpoint
3. **Basic Feed** - FeedScreen showing posts (no interaction)
4. **Post Widget** - PostBlock with full rendering
5. **Navigation** - Menu bar, view switching, history
6. **Post Mode** - Focus cycling within posts
7. **Actions** - Like, hide, navigate to user
8. **Comments** - Display, truncation, expansion
9. **Editor** - Compose block, comment creation
10. **Edit/Delete** - Modify own content
11. **Notifications** - NotificationsScreen
12. **Search & Directs** - Remaining views
13. **Polish** - Error handling, edge cases, styling
