# FreeFood Console Client - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a cross-platform TUI client for FreeFeed.net social network with reading, posting, commenting, and basic social features.

**Architecture:** Three-layer design (UI → State → API). Textual handles TUI rendering and input. httpx handles async HTTP. Data flows from API through denormalization into dataclass models displayed by widgets.

**Tech Stack:** Python 3.11+, Textual (TUI), httpx (HTTP), platformdirs (config paths), pytest (testing)

**Reference Docs:**
- Design: `docs/plans/2026-01-24-freefood-design.md`
- Python spec: `docs/plans/2026-01-24-freefood-python-implementation.md`
- API: `../frfc/docs/freefeed-api.md`

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `freefood/__init__.py`
- Create: `freefood/__main__.py`
- Create: `tests/__init__.py`

**Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "freefood"
version = "0.1.0"
description = "Console client for FreeFeed.net"
requires-python = ">=3.11"
license = "MIT"
authors = [
    { name = "Alex Kapranoff", email = "kapranoff@gmail.com" }
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
]

[project.scripts]
freefood = "freefood.__main__:main"

[tool.hatch.build.targets.wheel]
packages = ["freefood"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

**Step 2: Create package init**

Create `freefood/__init__.py`:
```python
"""FreeFood - Console client for FreeFeed.net"""

__version__ = "0.1.0"
```

**Step 3: Create entry point stub**

Create `freefood/__main__.py`:
```python
"""Entry point for freefood console client."""


def main() -> None:
    """Run the FreeFood application."""
    print("FreeFood starting...")


if __name__ == "__main__":
    main()
```

**Step 4: Create tests init**

Create `tests/__init__.py`:
```python
"""Tests for FreeFood console client."""
```

**Step 5: Create virtual environment and install**

Run:
```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
```

**Step 6: Verify installation**

Run: `freefood`
Expected: "FreeFood starting..."

**Step 7: Commit**

```bash
git add pyproject.toml freefood/ tests/
git commit -m "$(cat <<'EOF'
feat: initial project scaffolding

- pyproject.toml with dependencies
- Package structure with entry point
- Test directory
EOF
)"
```

---

## Task 2: Configuration Module

**Files:**
- Create: `freefood/config.py`
- Create: `tests/test_config.py`

**Step 1: Write failing test for get_config_path**

Create `tests/test_config.py`:
```python
"""Tests for configuration module."""

from pathlib import Path

from freefood.config import get_config_path


def test_get_config_path_returns_path():
    """Config path should be a Path object."""
    path = get_config_path()
    assert isinstance(path, Path)


def test_get_config_path_ends_with_config_ini():
    """Config path should end with config.ini."""
    path = get_config_path()
    assert path.name == "config.ini"


def test_get_config_path_contains_freefood():
    """Config path should contain 'freefood' directory."""
    path = get_config_path()
    assert "freefood" in str(path)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with "cannot import name 'get_config_path'"

**Step 3: Implement get_config_path**

Create `freefood/config.py`:
```python
"""Configuration file handling for FreeFood."""

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
    return config_dir / "config.ini"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS (3 tests)

**Step 5: Write failing test for load/save config**

Add to `tests/test_config.py`:
```python
import tempfile
from unittest.mock import patch

from freefood.config import load_config, save_config, get_token, save_token


def test_load_config_returns_configparser():
    """load_config should return a ConfigParser."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("freefood.config.get_config_path", return_value=Path(tmpdir) / "config.ini"):
            config = load_config()
            assert isinstance(config, configparser.ConfigParser)


def test_save_and_load_config():
    """Saved config should be loadable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.ini"
        with patch("freefood.config.get_config_path", return_value=config_path):
            config = configparser.ConfigParser()
            config["test"] = {"key": "value"}
            save_config(config)

            loaded = load_config()
            assert loaded.get("test", "key") == "value"


def test_get_token_returns_none_when_missing():
    """get_token should return None if no token saved."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("freefood.config.get_config_path", return_value=Path(tmpdir) / "config.ini"):
            assert get_token() is None


def test_save_and_get_token():
    """Saved token should be retrievable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.ini"
        with patch("freefood.config.get_config_path", return_value=config_path):
            save_token("test-token-123", "testuser")
            assert get_token() == "test-token-123"
```

Add import at top:
```python
import configparser
```

**Step 6: Run test to verify it fails**

Run: `pytest tests/test_config.py::test_load_config_returns_configparser -v`
Expected: FAIL with "cannot import name 'load_config'"

**Step 7: Implement remaining config functions**

Update `freefood/config.py`:
```python
"""Configuration file handling for FreeFood."""

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
    config_path.parent.mkdir(parents=True, exist_ok=True)
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

**Step 8: Run all config tests**

Run: `pytest tests/test_config.py -v`
Expected: PASS (7 tests)

**Step 9: Commit**

```bash
git add freefood/config.py tests/test_config.py
git commit -m "$(cat <<'EOF'
feat: add configuration module

- XDG-compliant config path via platformdirs
- Load/save INI config files
- Token storage for authentication
EOF
)"
```

---

## Task 3: Data Models

**Files:**
- Create: `freefood/models.py`
- Create: `tests/test_models.py`

**Step 1: Write failing test for User model**

Create `tests/test_models.py`:
```python
"""Tests for data models."""

from datetime import datetime

from freefood.models import User, Comment, Post, View, HistoryEntry


def test_user_creation():
    """User should be created with required fields."""
    user = User(
        id="123",
        username="alice",
        screen_name="Alice Smith",
        type="user",
    )
    assert user.id == "123"
    assert user.username == "alice"
    assert user.screen_name == "Alice Smith"
    assert user.type == "user"
    assert user.profile_picture_url is None


def test_user_with_profile_picture():
    """User can have optional profile picture."""
    user = User(
        id="123",
        username="alice",
        screen_name="Alice",
        type="user",
        profile_picture_url="https://example.com/pic.jpg",
    )
    assert user.profile_picture_url == "https://example.com/pic.jpg"


def test_group_user():
    """User with type='group' represents a group."""
    group = User(
        id="456",
        username="devs",
        screen_name="Developers",
        type="group",
    )
    assert group.type == "group"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py::test_user_creation -v`
Expected: FAIL with "cannot import name 'User'"

**Step 3: Implement User model**

Create `freefood/models.py`:
```python
"""Data models for FreeFood."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


@dataclass
class User:
    """A FreeFeed user or group."""

    id: str
    username: str
    screen_name: str
    type: str  # "user" or "group"
    profile_picture_url: str | None = None
```

**Step 4: Run User tests**

Run: `pytest tests/test_models.py -v -k user`
Expected: PASS (3 tests)

**Step 5: Write failing test for Comment model**

Add to `tests/test_models.py`:
```python
def test_comment_creation():
    """Comment should be created with required fields."""
    author = User(id="1", username="bob", screen_name="Bob", type="user")
    comment = Comment(
        id="c1",
        body="Great post!",
        author=author,
        created_at=datetime(2026, 1, 24, 12, 0, 0),
        likes=5,
    )
    assert comment.id == "c1"
    assert comment.body == "Great post!"
    assert comment.author.username == "bob"
    assert comment.likes == 5
    assert comment.is_liked is False
    assert comment.is_own is False


def test_comment_own_flag():
    """Comment can be marked as user's own."""
    author = User(id="1", username="me", screen_name="Me", type="user")
    comment = Comment(
        id="c1",
        body="My comment",
        author=author,
        created_at=datetime.now(),
        likes=0,
        is_own=True,
    )
    assert comment.is_own is True
```

**Step 6: Run test to verify it fails**

Run: `pytest tests/test_models.py::test_comment_creation -v`
Expected: FAIL with "cannot import name 'Comment'"

**Step 7: Implement Comment model**

Add to `freefood/models.py`:
```python
@dataclass
class Comment:
    """A comment on a post."""

    id: str
    body: str
    author: User
    created_at: datetime
    likes: int
    is_liked: bool = False
    is_own: bool = False
```

**Step 8: Run Comment tests**

Run: `pytest tests/test_models.py -v -k comment`
Expected: PASS (2 tests)

**Step 9: Write failing test for Post model**

Add to `tests/test_models.py`:
```python
def test_post_creation():
    """Post should be created with required fields."""
    author = User(id="1", username="alice", screen_name="Alice", type="user")
    group = User(id="2", username="news", screen_name="News", type="group")
    now = datetime(2026, 1, 24, 12, 0, 0)

    post = Post(
        id="p1",
        body="Hello world!",
        author=author,
        groups=[group],
        created_at=now,
        updated_at=now,
        comments=[],
        omitted_comments=0,
        omitted_likes=0,
        likes=[],
    )
    assert post.id == "p1"
    assert post.body == "Hello world!"
    assert post.author.username == "alice"
    assert len(post.groups) == 1
    assert post.groups[0].username == "news"
    assert post.is_liked is False
    assert post.is_hidden is False
    assert post.is_own is False


def test_post_with_comments():
    """Post can contain comments."""
    author = User(id="1", username="alice", screen_name="Alice", type="user")
    commenter = User(id="2", username="bob", screen_name="Bob", type="user")
    now = datetime.now()

    comment = Comment(
        id="c1",
        body="Nice!",
        author=commenter,
        created_at=now,
        likes=1,
    )
    post = Post(
        id="p1",
        body="My post",
        author=author,
        groups=[],
        created_at=now,
        updated_at=now,
        comments=[comment],
        omitted_comments=5,
        omitted_likes=10,
        likes=[commenter],
    )
    assert len(post.comments) == 1
    assert post.comments[0].body == "Nice!"
    assert post.omitted_comments == 5
    assert post.omitted_likes == 10
    assert len(post.likes) == 1
```

**Step 10: Run test to verify it fails**

Run: `pytest tests/test_models.py::test_post_creation -v`
Expected: FAIL with "cannot import name 'Post'"

**Step 11: Implement Post model**

Add to `freefood/models.py`:
```python
@dataclass
class Post:
    """A FreeFeed post."""

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
```

**Step 12: Run Post tests**

Run: `pytest tests/test_models.py -v -k post`
Expected: PASS (2 tests)

**Step 13: Write failing test for View enum and HistoryEntry**

Add to `tests/test_models.py`:
```python
def test_view_enum():
    """View enum should have all required values."""
    assert View.HOME.value == "home"
    assert View.NOTIFICATIONS.value == "notifications"
    assert View.DIRECTS.value == "directs"
    assert View.SEARCH.value == "search"
    assert View.USER_FEED.value == "user_feed"
    assert View.GROUP_FEED.value == "group_feed"


def test_history_entry():
    """HistoryEntry should store navigation state."""
    entry = HistoryEntry(
        view=View.USER_FEED,
        target="alice",
        scroll_position=42,
        query=None,
    )
    assert entry.view == View.USER_FEED
    assert entry.target == "alice"
    assert entry.scroll_position == 42


def test_history_entry_for_search():
    """HistoryEntry for search should store query."""
    entry = HistoryEntry(
        view=View.SEARCH,
        target=None,
        scroll_position=0,
        query="python",
    )
    assert entry.query == "python"
```

**Step 14: Run test to verify it fails**

Run: `pytest tests/test_models.py::test_view_enum -v`
Expected: FAIL with "cannot import name 'View'"

**Step 15: Implement View and HistoryEntry**

Add to `freefood/models.py`:
```python
class View(Enum):
    """Application view types."""

    HOME = "home"
    NOTIFICATIONS = "notifications"
    DIRECTS = "directs"
    SEARCH = "search"
    USER_FEED = "user_feed"
    GROUP_FEED = "group_feed"


@dataclass
class HistoryEntry:
    """Navigation history entry."""

    view: View
    target: str | None  # username/group for USER_FEED/GROUP_FEED
    scroll_position: int
    query: str | None = None  # for SEARCH
```

**Step 16: Run all model tests**

Run: `pytest tests/test_models.py -v`
Expected: PASS (10 tests)

**Step 17: Commit**

```bash
git add freefood/models.py tests/test_models.py
git commit -m "$(cat <<'EOF'
feat: add data models

- User model (users and groups)
- Comment model with likes and ownership
- Post model with full structure
- View enum and HistoryEntry for navigation
EOF
)"
```

---

## Task 4: API Client - Core

**Files:**
- Create: `freefood/api.py`
- Create: `tests/test_api.py`

**Step 1: Write failing test for API client initialization**

Create `tests/test_api.py`:
```python
"""Tests for FreeFeed API client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from freefood.api import FreeFeedAPI
from freefood.models import User


def test_api_client_initialization():
    """API client should initialize with token."""
    api = FreeFeedAPI("test-token")
    assert api.token == "test-token"
    assert api.current_user is None


def test_api_client_base_url():
    """API client should have correct base URL."""
    api = FreeFeedAPI("test-token")
    assert api.BASE_URL == "https://freefeed.net"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py::test_api_client_initialization -v`
Expected: FAIL with "cannot import name 'FreeFeedAPI'"

**Step 3: Implement basic API client**

Create `freefood/api.py`:
```python
"""FreeFeed API client."""

from datetime import datetime

import httpx

from .models import User, Comment, Post


class FreeFeedAPI:
    """Async client for FreeFeed API."""

    BASE_URL = "https://freefeed.net"

    def __init__(self, token: str) -> None:
        """Initialize API client with auth token."""
        self.token = token
        self.current_user: User | None = None
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
```

**Step 4: Run initialization tests**

Run: `pytest tests/test_api.py -v`
Expected: PASS (2 tests)

**Step 5: Write failing test for validate_token**

Add to `tests/test_api.py`:
```python
@pytest.mark.asyncio
async def test_validate_token_success():
    """validate_token should return User on success."""
    api = FreeFeedAPI("test-token")

    mock_response = {
        "users": {
            "id": "user-123",
            "username": "testuser",
            "screenName": "Test User",
            "type": "user",
        }
    }

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        user = await api.validate_token()

        assert user.id == "user-123"
        assert user.username == "testuser"
        assert user.screen_name == "Test User"
        assert api.current_user == user
        mock_client.get.assert_called_once_with("/v2/users/whoami")
```

**Step 6: Run test to verify it fails**

Run: `pytest tests/test_api.py::test_validate_token_success -v`
Expected: FAIL with "FreeFeedAPI object has no attribute 'validate_token'"

**Step 7: Implement validate_token and user parsing**

Add to `freefood/api.py` class:
```python
    async def validate_token(self) -> User:
        """Validate token and return current user."""
        client = await self._get_client()
        response = await client.get("/v2/users/whoami")
        response.raise_for_status()
        data = response.json()
        self.current_user = self._parse_user(data["users"])
        return self.current_user

    def _parse_user(self, data: dict) -> User:
        """Parse user data from API response."""
        return User(
            id=data["id"],
            username=data["username"],
            screen_name=data.get("screenName", data["username"]),
            type=data.get("type", "user"),
            profile_picture_url=data.get("profilePictureMediumUrl"),
        )
```

**Step 8: Run validate_token test**

Run: `pytest tests/test_api.py::test_validate_token_success -v`
Expected: PASS

**Step 9: Commit**

```bash
git add freefood/api.py tests/test_api.py
git commit -m "$(cat <<'EOF'
feat: add API client with token validation

- FreeFeedAPI class with async httpx client
- Token validation via /v2/users/whoami
- User parsing from API response
EOF
)"
```

---

## Task 5: API Client - Feed Fetching

**Files:**
- Modify: `freefood/api.py`
- Modify: `tests/test_api.py`

**Step 1: Write failing test for denormalize_posts**

Add to `tests/test_api.py`:
```python
@pytest.mark.asyncio
async def test_denormalize_posts():
    """denormalize_posts should join normalized data."""
    api = FreeFeedAPI("test-token")
    api.current_user = User(
        id="me-123",
        username="me",
        screen_name="Me",
        type="user",
    )

    normalized_data = {
        "posts": [
            {
                "id": "post-1",
                "body": "Hello world",
                "createdBy": "user-1",
                "createdAt": "1706097600000",
                "updatedAt": "1706097600000",
                "comments": ["comment-1"],
                "likes": ["user-2"],
                "postedTo": ["feed-1"],
                "omittedComments": 0,
                "omittedLikes": 0,
            }
        ],
        "comments": [
            {
                "id": "comment-1",
                "body": "Nice post!",
                "createdBy": "user-2",
                "createdAt": "1706097700000",
                "likes": 3,
            }
        ],
        "users": [
            {"id": "user-1", "username": "alice", "screenName": "Alice", "type": "user"},
            {"id": "user-2", "username": "bob", "screenName": "Bob", "type": "user"},
            {"id": "feed-1", "username": "news", "screenName": "News", "type": "group"},
        ],
    }

    posts = api._denormalize_posts(normalized_data)

    assert len(posts) == 1
    post = posts[0]
    assert post.id == "post-1"
    assert post.body == "Hello world"
    assert post.author.username == "alice"
    assert len(post.comments) == 1
    assert post.comments[0].body == "Nice post!"
    assert post.comments[0].author.username == "bob"
    assert len(post.groups) == 1
    assert post.groups[0].username == "news"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py::test_denormalize_posts -v`
Expected: FAIL with "FreeFeedAPI object has no attribute '_denormalize_posts'"

**Step 3: Implement denormalize_posts**

Add to `freefood/api.py` class:
```python
    def _parse_comment(self, data: dict, users_by_id: dict[str, User]) -> Comment:
        """Parse comment data from API response."""
        author = users_by_id.get(data["createdBy"])
        is_own = (
            author is not None
            and self.current_user is not None
            and author.id == self.current_user.id
        )
        return Comment(
            id=data["id"],
            body=data["body"],
            author=author,
            created_at=datetime.fromtimestamp(int(data["createdAt"]) / 1000),
            likes=data.get("likes", 0),
            is_liked=data.get("hasOwnLike", False),
            is_own=is_own,
        )

    def _denormalize_posts(self, data: dict) -> list[Post]:
        """Convert normalized API response to Post objects."""
        # Build lookup dicts
        users_by_id = {u["id"]: self._parse_user(u) for u in data.get("users", [])}
        comments_by_id = {
            c["id"]: self._parse_comment(c, users_by_id)
            for c in data.get("comments", [])
        }

        posts = []
        for p in data.get("posts", []):
            author = users_by_id.get(p["createdBy"])
            post_comments = [
                comments_by_id[cid]
                for cid in p.get("comments", [])
                if cid in comments_by_id
            ]
            post_likes = [
                users_by_id[uid] for uid in p.get("likes", []) if uid in users_by_id
            ]
            groups = [
                users_by_id[fid]
                for fid in p.get("postedTo", [])
                if fid in users_by_id and users_by_id[fid].type == "group"
            ]
            is_own = (
                author is not None
                and self.current_user is not None
                and author.id == self.current_user.id
            )

            posts.append(
                Post(
                    id=p["id"],
                    body=p["body"],
                    author=author,
                    groups=groups,
                    created_at=datetime.fromtimestamp(int(p["createdAt"]) / 1000),
                    updated_at=datetime.fromtimestamp(int(p["updatedAt"]) / 1000),
                    comments=post_comments,
                    omitted_comments=p.get("omittedComments", 0),
                    omitted_likes=p.get("omittedLikes", 0),
                    likes=post_likes,
                    is_liked=p.get("hasOwnLike", False),
                    is_hidden=p.get("isHidden", False),
                    is_own=is_own,
                )
            )
        return posts
```

**Step 4: Run denormalize test**

Run: `pytest tests/test_api.py::test_denormalize_posts -v`
Expected: PASS

**Step 5: Write failing test for get_home_feed**

Add to `tests/test_api.py`:
```python
@pytest.mark.asyncio
async def test_get_home_feed():
    """get_home_feed should return list of posts."""
    api = FreeFeedAPI("test-token")
    api.current_user = User(id="me", username="me", screen_name="Me", type="user")

    mock_response = {
        "posts": [
            {
                "id": "p1",
                "body": "Test post",
                "createdBy": "u1",
                "createdAt": "1706097600000",
                "updatedAt": "1706097600000",
                "comments": [],
                "likes": [],
                "postedTo": [],
                "omittedComments": 0,
                "omittedLikes": 0,
            }
        ],
        "comments": [],
        "users": [
            {"id": "u1", "username": "alice", "screenName": "Alice", "type": "user"},
        ],
    }

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        posts = await api.get_home_feed()

        assert len(posts) == 1
        assert posts[0].body == "Test post"
        mock_client.get.assert_called_once_with(
            "/v2/timelines/home", params={"offset": 0, "limit": 30}
        )
```

**Step 6: Run test to verify it fails**

Run: `pytest tests/test_api.py::test_get_home_feed -v`
Expected: FAIL with "FreeFeedAPI object has no attribute 'get_home_feed'"

**Step 7: Implement get_home_feed**

Add to `freefood/api.py` class:
```python
    async def get_home_feed(self, offset: int = 0, limit: int = 30) -> list[Post]:
        """Fetch home timeline."""
        client = await self._get_client()
        response = await client.get(
            "/v2/timelines/home", params={"offset": offset, "limit": limit}
        )
        response.raise_for_status()
        return self._denormalize_posts(response.json())
```

**Step 8: Run get_home_feed test**

Run: `pytest tests/test_api.py::test_get_home_feed -v`
Expected: PASS

**Step 9: Implement remaining feed methods**

Add to `freefood/api.py` class:
```python
    async def get_user_feed(
        self, username: str, offset: int = 0, limit: int = 30
    ) -> list[Post]:
        """Fetch user timeline."""
        client = await self._get_client()
        response = await client.get(
            f"/v2/timelines/{username}", params={"offset": offset, "limit": limit}
        )
        response.raise_for_status()
        return self._denormalize_posts(response.json())

    async def get_directs(self, offset: int = 0, limit: int = 30) -> list[Post]:
        """Fetch direct messages."""
        client = await self._get_client()
        response = await client.get(
            "/v2/timelines/filter/directs", params={"offset": offset, "limit": limit}
        )
        response.raise_for_status()
        return self._denormalize_posts(response.json())

    async def search(self, query: str, offset: int = 0, limit: int = 30) -> list[Post]:
        """Search posts."""
        client = await self._get_client()
        response = await client.get(
            "/v2/search", params={"q": query, "offset": offset, "limit": limit}
        )
        response.raise_for_status()
        return self._denormalize_posts(response.json())

    async def get_post(self, post_id: str) -> Post | None:
        """Fetch single post with all comments."""
        client = await self._get_client()
        response = await client.get(
            f"/v2/posts/{post_id}", params={"maxComments": "all", "maxLikes": "all"}
        )
        response.raise_for_status()
        posts = self._denormalize_posts(response.json())
        return posts[0] if posts else None
```

**Step 10: Run all API tests**

Run: `pytest tests/test_api.py -v`
Expected: PASS (5 tests)

**Step 11: Commit**

```bash
git add freefood/api.py tests/test_api.py
git commit -m "$(cat <<'EOF'
feat: add feed fetching to API client

- Denormalize posts from API response
- get_home_feed, get_user_feed, get_directs
- search and get_post methods
EOF
)"
```

---

## Task 6: API Client - Actions

**Files:**
- Modify: `freefood/api.py`
- Modify: `tests/test_api.py`

**Step 1: Write failing test for like_post**

Add to `tests/test_api.py`:
```python
@pytest.mark.asyncio
async def test_like_post():
    """like_post should POST to correct endpoint."""
    api = FreeFeedAPI("test-token")

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        await api.like_post("post-123")

        mock_client.post.assert_called_once_with("/v2/posts/post-123/like")


@pytest.mark.asyncio
async def test_unlike_post():
    """unlike_post should POST to correct endpoint."""
    api = FreeFeedAPI("test-token")

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        await api.unlike_post("post-123")

        mock_client.post.assert_called_once_with("/v2/posts/post-123/unlike")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py::test_like_post -v`
Expected: FAIL with "FreeFeedAPI object has no attribute 'like_post'"

**Step 3: Implement post actions**

Add to `freefood/api.py` class:
```python
    async def like_post(self, post_id: str) -> None:
        """Like a post."""
        client = await self._get_client()
        response = await client.post(f"/v2/posts/{post_id}/like")
        response.raise_for_status()

    async def unlike_post(self, post_id: str) -> None:
        """Unlike a post."""
        client = await self._get_client()
        response = await client.post(f"/v2/posts/{post_id}/unlike")
        response.raise_for_status()

    async def hide_post(self, post_id: str) -> None:
        """Hide a post."""
        client = await self._get_client()
        response = await client.post(f"/v2/posts/{post_id}/hide")
        response.raise_for_status()

    async def unhide_post(self, post_id: str) -> None:
        """Unhide a post."""
        client = await self._get_client()
        response = await client.post(f"/v2/posts/{post_id}/unhide")
        response.raise_for_status()
```

**Step 4: Run post action tests**

Run: `pytest tests/test_api.py -v -k "like_post or unlike_post"`
Expected: PASS (2 tests)

**Step 5: Write failing test for create_post**

Add to `tests/test_api.py`:
```python
@pytest.mark.asyncio
async def test_create_post():
    """create_post should POST with correct body."""
    api = FreeFeedAPI("test-token")
    api.current_user = User(id="me", username="me", screen_name="Me", type="user")

    mock_response = {
        "posts": [
            {
                "id": "new-post",
                "body": "Hello!",
                "createdBy": "me",
                "createdAt": "1706097600000",
                "updatedAt": "1706097600000",
                "comments": [],
                "likes": [],
                "postedTo": [],
                "omittedComments": 0,
                "omittedLikes": 0,
            }
        ],
        "users": [{"id": "me", "username": "me", "screenName": "Me", "type": "user"}],
        "comments": [],
    }

    with patch.object(api, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response_obj)
        mock_get_client.return_value = mock_client

        post = await api.create_post("Hello!", ["news"])

        assert post.body == "Hello!"
        mock_client.post.assert_called_once_with(
            "/v2/posts",
            json={"post": {"body": "Hello!"}, "meta": {"feeds": ["news"]}},
        )
```

**Step 6: Run test to verify it fails**

Run: `pytest tests/test_api.py::test_create_post -v`
Expected: FAIL with "FreeFeedAPI object has no attribute 'create_post'"

**Step 7: Implement post CRUD**

Add to `freefood/api.py` class:
```python
    async def create_post(self, body: str, feeds: list[str]) -> Post:
        """Create a new post."""
        client = await self._get_client()
        response = await client.post(
            "/v2/posts", json={"post": {"body": body}, "meta": {"feeds": feeds}}
        )
        response.raise_for_status()
        posts = self._denormalize_posts(response.json())
        return posts[0]

    async def update_post(self, post_id: str, body: str) -> Post:
        """Update a post."""
        client = await self._get_client()
        response = await client.put(
            f"/v2/posts/{post_id}", json={"post": {"body": body}}
        )
        response.raise_for_status()
        posts = self._denormalize_posts(response.json())
        return posts[0]

    async def delete_post(self, post_id: str) -> None:
        """Delete a post."""
        client = await self._get_client()
        response = await client.delete(f"/v2/posts/{post_id}")
        response.raise_for_status()
```

**Step 8: Run create_post test**

Run: `pytest tests/test_api.py::test_create_post -v`
Expected: PASS

**Step 9: Implement comment actions**

Add to `freefood/api.py` class:
```python
    async def create_comment(self, post_id: str, body: str) -> Comment:
        """Create a comment on a post."""
        client = await self._get_client()
        response = await client.post(
            "/v2/comments", json={"comment": {"body": body, "postId": post_id}}
        )
        response.raise_for_status()
        data = response.json()
        # Comment response includes users array
        users_by_id = {u["id"]: self._parse_user(u) for u in data.get("users", [])}
        return self._parse_comment(data["comments"], users_by_id)

    async def update_comment(self, comment_id: str, body: str) -> None:
        """Update a comment."""
        client = await self._get_client()
        response = await client.put(
            f"/v2/comments/{comment_id}", json={"comment": {"body": body}}
        )
        response.raise_for_status()

    async def delete_comment(self, comment_id: str) -> None:
        """Delete a comment."""
        client = await self._get_client()
        response = await client.delete(f"/v2/comments/{comment_id}")
        response.raise_for_status()

    async def like_comment(self, comment_id: str) -> None:
        """Like a comment."""
        client = await self._get_client()
        response = await client.post(f"/v2/comments/{comment_id}/like")
        response.raise_for_status()

    async def unlike_comment(self, comment_id: str) -> None:
        """Unlike a comment."""
        client = await self._get_client()
        response = await client.post(f"/v2/comments/{comment_id}/unlike")
        response.raise_for_status()
```

**Step 10: Implement subscription actions**

Add to `freefood/api.py` class:
```python
    async def subscribe(self, username: str) -> None:
        """Subscribe to a user."""
        client = await self._get_client()
        response = await client.post(f"/v2/users/{username}/subscribe")
        response.raise_for_status()

    async def unsubscribe(self, username: str) -> None:
        """Unsubscribe from a user."""
        client = await self._get_client()
        response = await client.post(f"/v2/users/{username}/unsubscribe")
        response.raise_for_status()
```

**Step 11: Run all API tests**

Run: `pytest tests/test_api.py -v`
Expected: PASS (8 tests)

**Step 12: Commit**

```bash
git add freefood/api.py tests/test_api.py
git commit -m "$(cat <<'EOF'
feat: add actions to API client

- Post: create, update, delete, like, unlike, hide, unhide
- Comment: create, update, delete, like, unlike
- User: subscribe, unsubscribe
EOF
)"
```

---

## Task 7: Basic Textual App Shell

**Files:**
- Create: `freefood/app.py`
- Create: `freefood/app.tcss`
- Modify: `freefood/__main__.py`

**Step 1: Create basic Textual app**

Create `freefood/app.py`:
```python
"""Main Textual application for FreeFood."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Static, Footer


class FreeFoodApp(App):
    """FreeFeed console client."""

    TITLE = "FreeFood"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("f5", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("FreeFood - Loading...", id="content")
        yield Footer()

    def action_refresh(self) -> None:
        """Refresh current view."""
        self.notify("Refreshing...")
```

**Step 2: Create basic CSS**

Create `freefood/app.tcss`:
```css
/* FreeFood TUI Styles */

Screen {
    background: $surface;
}

#content {
    width: 100%;
    height: 100%;
    content-align: center middle;
}

.loading {
    text-align: center;
    color: $text-muted;
}

.error {
    text-align: center;
    color: $error;
}
```

**Step 3: Update entry point**

Update `freefood/__main__.py`:
```python
"""Entry point for freefood console client."""

from freefood.app import FreeFoodApp


def main() -> None:
    """Run the FreeFood application."""
    app = FreeFoodApp()
    app.run()


if __name__ == "__main__":
    main()
```

**Step 4: Verify app runs**

Run: `freefood`
Expected: TUI opens with "FreeFood - Loading..." text, F5 shows notification, q quits

**Step 5: Commit**

```bash
git add freefood/app.py freefood/app.tcss freefood/__main__.py
git commit -m "$(cat <<'EOF'
feat: add basic Textual app shell

- FreeFoodApp with CSS styling
- F5 refresh and q quit bindings
- Footer with key hints
EOF
)"
```

---

## Task 8: Auth Screen

**Files:**
- Create: `freefood/screens/__init__.py`
- Create: `freefood/screens/auth.py`
- Modify: `freefood/app.py`

**Step 1: Create screens package**

Create `freefood/screens/__init__.py`:
```python
"""Screens for FreeFood application."""

from .auth import AuthScreen

__all__ = ["AuthScreen"]
```

**Step 2: Create auth screen**

Create `freefood/screens/auth.py`:
```python
"""Authentication screen for first-run setup."""

import webbrowser

from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from freefood.config import AUTH_URL, save_token


class AuthScreen(Screen):
    """Screen for authenticating with FreeFeed."""

    CSS = """
    AuthScreen {
        align: center middle;
    }

    #auth-container {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 1 2;
    }

    #auth-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #auth-instructions {
        margin-bottom: 1;
    }

    #token-input {
        margin: 1 0;
    }

    #auth-buttons {
        align: center middle;
        height: 3;
    }

    Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Create auth screen widgets."""
        with Center():
            with Vertical(id="auth-container"):
                yield Static("Welcome to FreeFood!", id="auth-title")
                yield Static(
                    "To connect your FreeFeed account:\n"
                    "1. Click 'Open Browser' to create an app token\n"
                    "2. Copy the token from FreeFeed\n"
                    "3. Paste it below and click 'Connect'",
                    id="auth-instructions",
                )
                yield Button("Open Browser", id="open-browser", variant="primary")
                yield Input(placeholder="Paste your token here...", id="token-input", password=True)
                yield Button("Connect", id="connect", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "open-browser":
            webbrowser.open(AUTH_URL)
            self.notify("Browser opened. Copy your token and paste it below.")
        elif event.button.id == "connect":
            self._attempt_connect()

    def _attempt_connect(self) -> None:
        """Try to connect with the entered token."""
        token_input = self.query_one("#token-input", Input)
        token = token_input.value.strip()

        if not token:
            self.notify("Please enter a token", severity="error")
            return

        # Store token and signal app to validate
        self.app.post_message(AuthScreen.TokenSubmitted(token))

    class TokenSubmitted:
        """Message sent when user submits a token."""

        def __init__(self, token: str) -> None:
            self.token = token
```

**Step 3: Update app to use auth screen**

Update `freefood/app.py`:
```python
"""Main Textual application for FreeFood."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Static, Footer

from freefood.api import FreeFeedAPI
from freefood.config import get_token, save_token
from freefood.screens.auth import AuthScreen


class FreeFoodApp(App):
    """FreeFeed console client."""

    TITLE = "FreeFood"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("f5", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        """Initialize app."""
        super().__init__()
        self.api: FreeFeedAPI | None = None

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("FreeFood - Loading...", id="content")
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize app on startup."""
        token = get_token()
        if token:
            await self._try_connect(token)
        else:
            self.push_screen(AuthScreen())

    async def _try_connect(self, token: str) -> None:
        """Try to connect with token."""
        self.api = FreeFeedAPI(token)
        try:
            user = await self.api.validate_token()
            save_token(token, user.username)
            content = self.query_one("#content", Static)
            content.update(f"Connected as @{user.username}")
            self.notify(f"Welcome, {user.screen_name}!")
        except Exception as e:
            self.api = None
            self.notify(f"Connection failed: {e}", severity="error")
            self.push_screen(AuthScreen())

    async def on_auth_screen_token_submitted(
        self, message: AuthScreen.TokenSubmitted
    ) -> None:
        """Handle token submission from auth screen."""
        self.pop_screen()
        await self._try_connect(message.token)

    def action_refresh(self) -> None:
        """Refresh current view."""
        self.notify("Refreshing...")
```

**Step 4: Verify auth flow**

Run: `freefood`
Expected: Auth screen appears with Open Browser and Connect buttons

**Step 5: Commit**

```bash
git add freefood/screens/ freefood/app.py
git commit -m "$(cat <<'EOF'
feat: add authentication screen

- AuthScreen with browser-based token flow
- Token validation on connect
- Auto-check for existing token on startup
EOF
)"
```

---

## Task 9: Menu Bar Widget

**Files:**
- Create: `freefood/widgets/__init__.py`
- Create: `freefood/widgets/menu.py`
- Modify: `freefood/app.tcss`

**Step 1: Create widgets package**

Create `freefood/widgets/__init__.py`:
```python
"""Widgets for FreeFood application."""

from .menu import MenuBar

__all__ = ["MenuBar"]
```

**Step 2: Create menu bar widget**

Create `freefood/widgets/menu.py`:
```python
"""Menu bar widget for navigation."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button

from freefood.models import View


class MenuBar(Widget):
    """Top navigation menu bar."""

    DEFAULT_CSS = """
    MenuBar {
        dock: top;
        height: 3;
        background: $primary;
        padding: 0 1;
    }

    MenuBar Horizontal {
        height: 100%;
        align: left middle;
    }

    MenuBar Button {
        margin: 0 1 0 0;
        min-width: 14;
    }

    MenuBar Button.selected {
        background: $secondary;
    }

    MenuBar #back-button {
        min-width: 8;
    }
    """

    class ViewSelected(Message):
        """Message sent when a view is selected."""

        def __init__(self, view: View) -> None:
            self.view = view
            super().__init__()

    class BackRequested(Message):
        """Message sent when back is requested."""

        pass

    def __init__(self, current_view: View = View.HOME) -> None:
        """Initialize menu bar."""
        super().__init__()
        self.current_view = current_view

    def compose(self) -> ComposeResult:
        """Create menu buttons."""
        with Horizontal():
            yield Button("← Back", id="back-button", variant="default")
            yield Button("Home", id="home-button", variant="primary")
            yield Button("Notifications", id="notifications-button")
            yield Button("Directs", id="directs-button")
            yield Button("Search", id="search-button")

    def on_mount(self) -> None:
        """Highlight current view on mount."""
        self._update_selection()

    def _update_selection(self) -> None:
        """Update button selection state."""
        view_to_button = {
            View.HOME: "home-button",
            View.NOTIFICATIONS: "notifications-button",
            View.DIRECTS: "directs-button",
            View.SEARCH: "search-button",
        }

        for view, button_id in view_to_button.items():
            button = self.query_one(f"#{button_id}", Button)
            if view == self.current_view:
                button.add_class("selected")
            else:
                button.remove_class("selected")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_to_view = {
            "home-button": View.HOME,
            "notifications-button": View.NOTIFICATIONS,
            "directs-button": View.DIRECTS,
            "search-button": View.SEARCH,
        }

        if event.button.id == "back-button":
            self.post_message(self.BackRequested())
        elif event.button.id in button_to_view:
            view = button_to_view[event.button.id]
            if view != self.current_view:
                self.current_view = view
                self._update_selection()
                self.post_message(self.ViewSelected(view))

    def set_view(self, view: View) -> None:
        """Set current view externally."""
        self.current_view = view
        self._update_selection()
```

**Step 3: Update app CSS**

Update `freefood/app.tcss`:
```css
/* FreeFood TUI Styles */

Screen {
    background: $surface;
}

#content {
    width: 100%;
    height: 1fr;
    padding: 1;
}

.loading {
    text-align: center;
    color: $text-muted;
    height: 100%;
    content-align: center middle;
}

.error {
    text-align: center;
    color: $error;
    height: 100%;
    content-align: center middle;
}
```

**Step 4: Commit**

```bash
git add freefood/widgets/ freefood/app.tcss
git commit -m "$(cat <<'EOF'
feat: add menu bar widget

- MenuBar with Back, Home, Notifications, Directs, Search
- ViewSelected and BackRequested messages
- Selection highlighting
EOF
)"
```

---

## Task 10: Feed Screen (Basic)

**Files:**
- Create: `freefood/screens/feed.py`
- Modify: `freefood/screens/__init__.py`
- Modify: `freefood/app.py`

**Step 1: Create feed screen**

Create `freefood/screens/feed.py`:
```python
"""Feed screen for displaying posts."""

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.screen import Screen
from textual.widgets import Static

from freefood.models import View, Post
from freefood.widgets.menu import MenuBar


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

    .post-placeholder {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
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
                    # Temporary: simple post display
                    post_text = f"@{post.author.username}:\n{post.body[:200]}..."
                    container.mount(Static(post_text, classes="post-placeholder"))

        except Exception as e:
            container.remove_children()
            container.mount(
                Static(f"⚠ Failed to load: {e}\nPress F5 to retry", classes="error")
            )

    def action_focus_menu(self) -> None:
        """Focus the menu bar."""
        self.query_one(MenuBar).focus()

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
```

**Step 2: Update screens init**

Update `freefood/screens/__init__.py`:
```python
"""Screens for FreeFood application."""

from .auth import AuthScreen
from .feed import FeedScreen

__all__ = ["AuthScreen", "FeedScreen"]
```

**Step 3: Update app to use feed screen**

Update `freefood/app.py`:
```python
"""Main Textual application for FreeFood."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer

from freefood.api import FreeFeedAPI
from freefood.config import get_token, save_token
from freefood.screens.auth import AuthScreen
from freefood.screens.feed import FeedScreen


class FreeFoodApp(App):
    """FreeFeed console client."""

    TITLE = "FreeFood"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        """Initialize app."""
        super().__init__()
        self.api: FreeFeedAPI | None = None

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize app on startup."""
        token = get_token()
        if token:
            await self._try_connect(token)
        else:
            self.push_screen(AuthScreen())

    async def _try_connect(self, token: str) -> None:
        """Try to connect with token."""
        self.api = FreeFeedAPI(token)
        try:
            user = await self.api.validate_token()
            save_token(token, user.username)
            self.push_screen(FeedScreen())
            self.notify(f"Welcome, {user.screen_name}!")
        except Exception as e:
            self.api = None
            self.notify(f"Connection failed: {e}", severity="error")
            self.push_screen(AuthScreen())

    async def on_auth_screen_token_submitted(
        self, message: AuthScreen.TokenSubmitted
    ) -> None:
        """Handle token submission from auth screen."""
        self.pop_screen()
        await self._try_connect(message.token)
```

**Step 4: Verify feed loads**

Run: `freefood`
Expected: After auth, feed screen shows with menu bar and posts (or loading state)

**Step 5: Commit**

```bash
git add freefood/screens/feed.py freefood/screens/__init__.py freefood/app.py
git commit -m "$(cat <<'EOF'
feat: add basic feed screen

- FeedScreen with MenuBar
- Load and display posts from API
- View switching between Home and Directs
- Loading and error states
EOF
)"
```

---

## Task 11: Post Widget (Display Only)

**Files:**
- Create: `freefood/widgets/post.py`
- Modify: `freefood/widgets/__init__.py`
- Modify: `freefood/screens/feed.py`

**Step 1: Create post widget**

Create `freefood/widgets/post.py`:
```python
"""Post block widget for displaying posts."""

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from freefood.models import Post, Comment


def format_time_ago(dt: datetime) -> str:
    """Format datetime as relative time."""
    now = datetime.now()
    diff = now - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        mins = int(seconds / 60)
        return f"{mins}m ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}h ago"
    else:
        days = int(seconds / 86400)
        return f"{days}d ago"


class PostBlock(Widget, can_focus=True):
    """Widget displaying a single post."""

    DEFAULT_CSS = """
    PostBlock {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
        height: auto;
    }

    PostBlock:focus {
        border: solid $accent;
    }

    PostBlock .post-header {
        color: $text;
        text-style: bold;
    }

    PostBlock .post-body {
        margin: 1 0;
    }

    PostBlock .post-meta {
        color: $text-muted;
    }

    PostBlock .post-likes {
        color: $text-muted;
        margin-top: 1;
    }

    PostBlock .comment {
        margin-top: 1;
        padding-left: 2;
        border-left: solid $primary;
    }

    PostBlock .comment-likes {
        color: $error;
    }

    PostBlock .more-comments {
        text-align: center;
        color: $text-muted;
        margin: 1 0;
    }
    """

    MAX_BODY_LINES = 50
    MAX_COMMENT_LINES = 10

    class Selected(Message):
        """Message sent when post is selected."""

        def __init__(self, post: Post) -> None:
            self.post = post
            super().__init__()

    def __init__(self, post: Post) -> None:
        """Initialize post widget."""
        super().__init__()
        self.post = post
        self.body_expanded = False
        self.comments_expanded = False

    def compose(self) -> ComposeResult:
        """Create post widgets."""
        with Vertical():
            # Header
            header = self._format_header()
            yield Static(header, classes="post-header")

            # Body
            body = self._format_body()
            yield Static(body, classes="post-body")

            # Meta (time, actions placeholder)
            meta = format_time_ago(self.post.created_at)
            yield Static(meta, classes="post-meta")

            # Likes
            if self.post.likes:
                likes_text = self._format_likes()
                yield Static(likes_text, classes="post-likes")

            # Comments
            yield from self._render_comments()

    def _format_header(self) -> str:
        """Format post header."""
        author = f"@{self.post.author.username}"
        if self.post.groups:
            groups = ", ".join(f"@{g.username}" for g in self.post.groups)
            return f"{author} wrote in {groups}:"
        return f"{author} wrote:"

    def _format_body(self) -> str:
        """Format post body with truncation."""
        lines = self.post.body.split("\n")
        if len(lines) > self.MAX_BODY_LINES and not self.body_expanded:
            truncated = "\n".join(lines[: self.MAX_BODY_LINES])
            return f"{truncated}\n[show more...]"
        return self.post.body

    def _format_likes(self) -> str:
        """Format likes line."""
        likes = self.post.likes
        if len(likes) <= 3:
            names = ", ".join(f"@{u.username}" for u in likes)
            return f"♥ {names} liked this"
        else:
            names = ", ".join(f"@{u.username}" for u in likes[:3])
            others = len(likes) - 3 + self.post.omitted_likes
            return f"♥ {names} and {others} others liked this"

    def _render_comments(self):
        """Render comments section."""
        comments = self.post.comments
        total = len(comments) + self.post.omitted_comments

        if total == 0:
            return

        # Show first 2 and last 2
        if len(comments) <= 4 or self.comments_expanded:
            for comment in comments:
                yield self._render_comment(comment)
        else:
            # First 2
            for comment in comments[:2]:
                yield self._render_comment(comment)

            # Middle expander
            middle_count = total - 4
            yield Static(
                f"── {middle_count} more comments ──",
                classes="more-comments",
            )

            # Last 2
            for comment in comments[-2:]:
                yield self._render_comment(comment)

    def _render_comment(self, comment: Comment) -> Static:
        """Render a single comment."""
        lines = comment.body.split("\n")
        if len(lines) > self.MAX_COMMENT_LINES:
            body = "\n".join(lines[: self.MAX_COMMENT_LINES]) + "\n[show more...]"
        else:
            body = comment.body

        likes_str = f"[{comment.likes}♥]" if comment.likes else "[0♥]"
        text = f"{likes_str} {body} -- @{comment.author.username}"
        return Static(text, classes="comment")
```

**Step 2: Update widgets init**

Update `freefood/widgets/__init__.py`:
```python
"""Widgets for FreeFood application."""

from .menu import MenuBar
from .post import PostBlock

__all__ = ["MenuBar", "PostBlock"]
```

**Step 3: Update feed screen to use PostBlock**

Update `freefood/screens/feed.py`:
```python
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
                Static(f"⚠ Failed to load: {e}\nPress F5 to retry", classes="error")
            )

    def action_focus_menu(self) -> None:
        """Focus the menu bar."""
        self.query_one(MenuBar).focus()

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
```

**Step 4: Verify posts display**

Run: `freefood`
Expected: Posts display with proper formatting - header, body, time, likes, comments

**Step 5: Commit**

```bash
git add freefood/widgets/post.py freefood/widgets/__init__.py freefood/screens/feed.py
git commit -m "$(cat <<'EOF'
feat: add PostBlock widget

- Full post display with header, body, meta
- Likes formatting with user names
- Comments with first 2 + last 2 pattern
- Body and comment truncation
EOF
)"
```

---

## Remaining Tasks (Summary)

The plan continues with these additional tasks. Each follows the same TDD pattern:

### Task 12: Navigation State & History
- Add `state.py` with `AppState` class
- Implement history stack for Back navigation
- Wire up Back button in menu

### Task 13: Post Mode Focus System
- Add focusable elements to PostBlock
- Implement focus cycling with arrow keys
- Handle Enter/Escape for mode switching

### Task 14: Post Actions (Like, Hide)
- Add action buttons to PostBlock
- Wire up like/unlike/hide/unhide to API
- Update post state after action

### Task 15: Compose Block
- Create ComposeBlock widget
- Add to top of feed
- Wire up post creation

### Task 16: Inline Editor
- Create InlineEditor widget
- Handle multi-line input
- Tab navigation, Ctrl+Enter submit

### Task 17: Comment Creation
- Add comment button functionality
- Show editor after comments
- Wire up comment creation to API

### Task 18: Edit/Delete Posts
- Add Edit/Delete buttons for own posts
- Implement edit flow with pre-filled editor
- Implement delete with confirmation

### Task 19: Edit/Delete Comments
- Same as Task 18 but for comments

### Task 20: User/Group Feed Navigation
- Make usernames clickable
- Load user/group feed on click
- Add to history stack

### Task 21: Search View
- Add search input to feed screen
- Implement search results display
- Persist query between visits

### Task 22: Notifications Screen
- Create NotificationBlock widget
- Create NotificationsScreen
- Handle different notification types

### Task 23: Polish & Error Handling
- Improve error messages
- Add loading spinners
- Handle edge cases
- Final testing on all platforms

---

## Testing Checklist

Before release, verify on each platform:

- [ ] Linux: Run full flow (auth → browse → post → comment)
- [ ] macOS: Run full flow
- [ ] Windows: Run full flow
- [ ] Keyboard navigation works consistently
- [ ] All API endpoints verified against live server
- [ ] Error states display correctly
- [ ] Config file persists correctly

---

## API Verification Notes

Document any API discrepancies found during implementation here:

| Endpoint | Expected | Actual | Notes |
|----------|----------|--------|-------|
| | | | |

Update `../frfc/docs/freefeed-api.md` with any corrections.
