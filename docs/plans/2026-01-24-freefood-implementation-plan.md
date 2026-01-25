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

## Task 12: Navigation State & History

**Files:**
- Create: `freefood/state.py`
- Modify: `freefood/app.py`
- Modify: `freefood/screens/feed.py`
- Modify: `freefood/widgets/menu.py`

**Step 1: Create state module**

Create `freefood/state.py`:
```python
"""Application state management."""

from dataclasses import dataclass, field

from freefood.models import View, HistoryEntry


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

    def navigate_to(self, view: View, target: str | None = None, scroll_position: int = 0) -> None:
        """Navigate to a new view, pushing current to history."""
        self.push_history(scroll_position)
        self.current_view = view
        self.current_target = target
```

**Step 2: Add state to app**

Update `freefood/app.py` imports:
```python
from freefood.state import AppState
```

Add to `FreeFoodApp.__init__`:
```python
self.state = AppState()
```

**Step 3: Update FeedScreen to use state**

Update `freefood/screens/feed.py`:
- Accept `state: AppState` in `__init__` instead of `view: View`
- Use `self.state.current_view` instead of `self.current_view`
- On view change, call `self.state.navigate_to()`

**Step 4: Handle Back button**

Update `FeedScreen.on_menu_bar_back_requested`:
```python
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
```

**Step 5: Update app to pass state to FeedScreen**

In `app.py`, change `FeedScreen()` to `FeedScreen(self.state)`.

**Step 6: Verify back navigation**

Run app, navigate Home → Directs → Back. Should return to Home.

**Step 7: Commit**

```bash
git add freefood/state.py freefood/app.py freefood/screens/feed.py
git commit -m "feat: add navigation state and history

- AppState class with history stack
- Back button pops history and restores view
- Max 50 history entries"
```

---

## Task 13: Post Mode Focus System

**Files:**
- Modify: `freefood/widgets/post.py`
- Modify: `freefood/screens/feed.py`

**Step 1: Add focusable action elements to PostBlock**

The PostBlock already has `can_focus=True`. Now add individual focusable elements inside it.

Update `freefood/widgets/post.py` compose method to yield focusable elements:
```python
from textual.widgets import Button

def compose(self) -> ComposeResult:
    """Create post widgets."""
    with Vertical():
        # Header
        yield Static(self._format_header(), classes="post-header")

        # Body
        body_text = self._format_body()
        yield Static(body_text, classes="post-body")
        if self._body_is_truncated():
            yield Button("Show more...", id="show-more-body", classes="show-more")

        # Meta line with action buttons
        with Horizontal(classes="post-actions"):
            yield Static(format_time_ago(self.post.created_at), classes="post-meta")
            yield Button("Comment", id="btn-comment")
            like_label = "Unlike" if self.post.is_liked else "Like"
            yield Button(f"♥ {like_label}", id="btn-like")
            hide_label = "Unhide" if self.post.is_hidden else "Hide"
            yield Button(hide_label, id="btn-hide")
            if self.post.is_own:
                yield Button("Edit", id="btn-edit")
                yield Button("Delete", id="btn-delete")

        # Likes
        if self.post.likes:
            yield Static(self._format_likes(), classes="post-likes")

        # Comments
        yield from self._render_comments()

def _body_is_truncated(self) -> bool:
    """Check if body exceeds max lines."""
    lines = self.post.body.split("\n")
    return len(lines) > self.MAX_BODY_LINES and not self.body_expanded
```

**Step 2: Add CSS for action buttons**

Add to PostBlock `DEFAULT_CSS`:
```css
PostBlock .post-actions {
    height: auto;
    margin-top: 1;
}

PostBlock .post-actions Button {
    min-width: 10;
    margin-right: 1;
}

PostBlock .show-more {
    color: $text-muted;
    margin: 0;
}

PostBlock Button:focus {
    background: $accent;
}
```

**Step 3: Add key bindings for post mode**

Add bindings to PostBlock:
```python
BINDINGS = [
    ("up", "focus_previous", "Previous"),
    ("down", "focus_next", "Next"),
    ("escape", "exit_post_mode", "Back to feed"),
]
```

Implement actions:
```python
def action_focus_previous(self) -> None:
    """Focus previous focusable element."""
    self.screen.focus_previous()

def action_focus_next(self) -> None:
    """Focus next focusable element."""
    self.screen.focus_next()

def action_exit_post_mode(self) -> None:
    """Exit post mode, return focus to this post block."""
    self.focus()
```

**Step 4: Handle "show more" for body**

```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    """Handle button presses."""
    if event.button.id == "show-more-body":
        self.body_expanded = True
        self.refresh(recompose=True)
    elif event.button.id == "show-more-comments":
        # Will be implemented with API call
        self.comments_expanded = True
        self.post_message(self.ExpandComments(self.post))
```

**Step 5: Add message for comment expansion**

```python
class ExpandComments(Message):
    """Request to load all comments for a post."""
    def __init__(self, post: Post) -> None:
        self.post = post
        super().__init__()
```

**Step 6: Handle expand comments in FeedScreen**

```python
async def on_post_block_expand_comments(self, message: PostBlock.ExpandComments) -> None:
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
```

**Step 7: Commit**

```bash
git add freefood/widgets/post.py freefood/screens/feed.py
git commit -m "feat: add post mode focus system

- Action buttons in post (Comment, Like, Hide, Edit, Delete)
- Show more for truncated body
- Expand comments loads full post
- Up/Down navigate within post, Escape exits"
```

---

## Task 14: Post Actions (Like, Hide)

**Files:**
- Modify: `freefood/widgets/post.py`
- Modify: `freefood/screens/feed.py`

**Step 1: Add action messages to PostBlock**

```python
class LikeRequested(Message):
    """Request to like/unlike post."""
    def __init__(self, post: Post) -> None:
        self.post = post
        super().__init__()

class HideRequested(Message):
    """Request to hide/unhide post."""
    def __init__(self, post: Post) -> None:
        self.post = post
        super().__init__()
```

**Step 2: Handle button presses**

Add to `PostBlock.on_button_pressed`:
```python
elif event.button.id == "btn-like":
    self.post_message(self.LikeRequested(self.post))
elif event.button.id == "btn-hide":
    self.post_message(self.HideRequested(self.post))
```

**Step 3: Handle actions in FeedScreen**

```python
async def on_post_block_like_requested(self, message: PostBlock.LikeRequested) -> None:
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

async def on_post_block_hide_requested(self, message: PostBlock.HideRequested) -> None:
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
```

**Step 4: Verify actions**

Run app, like a post, verify button changes to "Unlike". Hide a post, verify it says "Unhide".

**Step 5: Commit**

```bash
git add freefood/widgets/post.py freefood/screens/feed.py
git commit -m "feat: add like and hide actions

- Like/Unlike toggles post like state
- Hide/Unhide toggles post hidden state
- Button labels update after action"
```

---

## Task 15: Compose Block

**Files:**
- Create: `freefood/widgets/compose.py`
- Modify: `freefood/widgets/__init__.py`
- Modify: `freefood/screens/feed.py`

**Step 1: Create compose widget**

Create `freefood/widgets/compose.py`:
```python
"""Compose block widget for creating posts."""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input, TextArea


class ComposeBlock(Widget, can_focus=True):
    """Widget for composing new posts."""

    DEFAULT_CSS = """
    ComposeBlock {
        height: auto;
        border: solid $primary;
        padding: 1;
        margin: 0 0 1 0;
    }

    ComposeBlock:focus-within {
        border: solid $accent;
    }

    ComposeBlock TextArea {
        height: auto;
        min-height: 3;
        max-height: 10;
    }

    ComposeBlock .compose-footer {
        height: 3;
        margin-top: 1;
    }

    ComposeBlock .compose-footer Input {
        width: 1fr;
    }

    ComposeBlock .compose-footer Button {
        margin-left: 1;
    }
    """

    class PostSubmitted(Message):
        """Message sent when post is submitted."""
        def __init__(self, body: str, feeds: list[str]) -> None:
            self.body = body
            self.feeds = feeds
            super().__init__()

    def __init__(self, default_feed: str | None = None) -> None:
        """Initialize compose block."""
        super().__init__()
        self.default_feed = default_feed

    def compose(self) -> ComposeResult:
        """Create compose widgets."""
        with Vertical():
            yield TextArea(id="compose-text", language=None)
            with Horizontal(classes="compose-footer"):
                default = self.default_feed or ""
                yield Input(placeholder="Post to (comma-separated)", id="compose-feeds", value=default)
                yield Button("Post", id="btn-post", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle post button."""
        if event.button.id == "btn-post":
            self._submit()

    def _submit(self) -> None:
        """Submit the post."""
        text_area = self.query_one("#compose-text", TextArea)
        feeds_input = self.query_one("#compose-feeds", Input)

        body = text_area.text.strip()
        if not body:
            self.notify("Post cannot be empty", severity="error")
            return

        feeds_str = feeds_input.value.strip()
        feeds = [f.strip() for f in feeds_str.split(",") if f.strip()]

        if not feeds:
            self.notify("Please specify at least one feed", severity="error")
            return

        self.post_message(self.PostSubmitted(body, feeds))

    def clear(self) -> None:
        """Clear the compose block."""
        self.query_one("#compose-text", TextArea).clear()

    def on_key(self, event) -> None:
        """Handle Ctrl+Enter to submit."""
        if event.key == "ctrl+enter":
            self._submit()
            event.stop()
```

**Step 2: Update widgets init**

Add to `freefood/widgets/__init__.py`:
```python
from .compose import ComposeBlock

__all__ = ["MenuBar", "PostBlock", "ComposeBlock"]
```

**Step 3: Add compose block to FeedScreen**

Update `FeedScreen.compose`:
```python
def compose(self) -> ComposeResult:
    """Create feed screen widgets."""
    yield MenuBar(self.state.current_view)
    with ScrollableContainer(id="feed-container"):
        # Show compose block for Home and Directs
        if self.state.current_view in (View.HOME, View.DIRECTS):
            yield ComposeBlock()
        yield Static("Loading feed...", classes="loading")
```

**Step 4: Handle post submission**

```python
async def on_compose_block_post_submitted(self, message: ComposeBlock.PostSubmitted) -> None:
    """Handle new post submission."""
    try:
        await self.app.api.create_post(message.body, message.feeds)
        compose = self.query_one(ComposeBlock)
        compose.clear()
        self.notify("Posted!")
        self.run_worker(self.refresh_content())
    except Exception as e:
        self.notify(f"Failed to post: {e}", severity="error")
```

**Step 5: Commit**

```bash
git add freefood/widgets/compose.py freefood/widgets/__init__.py freefood/screens/feed.py
git commit -m "feat: add compose block for creating posts

- ComposeBlock with text area and feeds input
- Ctrl+Enter shortcut to submit
- Shows on Home and Directs views"
```

---

## Task 16: Inline Editor (Comment Editor)

**Files:**
- Create: `freefood/widgets/editor.py`
- Modify: `freefood/widgets/__init__.py`

**Step 1: Create inline editor widget**

Create `freefood/widgets/editor.py`:
```python
"""Inline editor widget for comments and edits."""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, TextArea


class InlineEditor(Widget, can_focus=True):
    """Inline editor for comments and post edits."""

    DEFAULT_CSS = """
    InlineEditor {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1 0;
    }

    InlineEditor TextArea {
        height: auto;
        min-height: 3;
        max-height: 15;
    }

    InlineEditor .editor-buttons {
        height: 3;
        align: right middle;
        margin-top: 1;
    }

    InlineEditor Button {
        margin-left: 1;
    }
    """

    class Submitted(Message):
        """Editor content submitted."""
        def __init__(self, text: str, context: dict) -> None:
            self.text = text
            self.context = context  # e.g., {"post_id": "..."} or {"comment_id": "..."}
            super().__init__()

    class Cancelled(Message):
        """Editor cancelled."""
        def __init__(self, context: dict) -> None:
            self.context = context
            super().__init__()

    def __init__(self, initial_text: str = "", context: dict | None = None, submit_label: str = "Submit") -> None:
        """Initialize editor."""
        super().__init__()
        self.initial_text = initial_text
        self.context = context or {}
        self.submit_label = submit_label

    def compose(self) -> ComposeResult:
        """Create editor widgets."""
        with Vertical():
            yield TextArea(self.initial_text, id="editor-text", language=None)
            with Horizontal(classes="editor-buttons"):
                yield Button("Cancel", id="btn-cancel")
                yield Button(self.submit_label, id="btn-submit", variant="primary")

    def on_mount(self) -> None:
        """Focus text area on mount."""
        self.query_one("#editor-text", TextArea).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-submit":
            self._submit()
        elif event.button.id == "btn-cancel":
            self._cancel()

    def on_key(self, event) -> None:
        """Handle keyboard shortcuts."""
        if event.key == "ctrl+enter":
            self._submit()
            event.stop()
        elif event.key == "escape":
            self._cancel()
            event.stop()

    def _submit(self) -> None:
        """Submit editor content."""
        text = self.query_one("#editor-text", TextArea).text.strip()
        if not text:
            self.notify("Cannot submit empty text", severity="error")
            return
        self.post_message(self.Submitted(text, self.context))

    def _cancel(self) -> None:
        """Cancel editing."""
        self.post_message(self.Cancelled(self.context))
```

**Step 2: Update widgets init**

```python
from .editor import InlineEditor

__all__ = ["MenuBar", "PostBlock", "ComposeBlock", "InlineEditor"]
```

**Step 3: Commit**

```bash
git add freefood/widgets/editor.py freefood/widgets/__init__.py
git commit -m "feat: add inline editor widget

- TextArea with Cancel/Submit buttons
- Ctrl+Enter to submit, Escape to cancel
- Configurable initial text and submit label"
```

---

## Task 17: Comment Creation

**Files:**
- Modify: `freefood/widgets/post.py`
- Modify: `freefood/screens/feed.py`

**Step 1: Add comment editor state to PostBlock**

```python
def __init__(self, post: Post) -> None:
    super().__init__()
    self.post = post
    self.body_expanded = False
    self.comments_expanded = False
    self.show_comment_editor = False
```

**Step 2: Update compose to show editor**

```python
def compose(self) -> ComposeResult:
    # ... existing code ...

    # Comments
    yield from self._render_comments()

    # Comment editor (shown when commenting)
    if self.show_comment_editor:
        yield InlineEditor(
            context={"post_id": self.post.id},
            submit_label="Comment"
        )
```

**Step 3: Handle Comment button**

```python
class CommentRequested(Message):
    """Request to show comment editor."""
    def __init__(self, post: Post) -> None:
        self.post = post
        super().__init__()

# In on_button_pressed:
elif event.button.id == "btn-comment":
    self.show_comment_editor = True
    self.refresh(recompose=True)
```

**Step 4: Handle editor submission in FeedScreen**

```python
async def on_inline_editor_submitted(self, message: InlineEditor.Submitted) -> None:
    """Handle editor submission."""
    context = message.context

    if "post_id" in context and "comment_id" not in context:
        # New comment
        try:
            await self.app.api.create_comment(context["post_id"], message.text)
            self.notify("Comment added!")
            # Refresh the post to show new comment
            await self._refresh_post(context["post_id"])
        except Exception as e:
            self.notify(f"Failed: {e}", severity="error")

def on_inline_editor_cancelled(self, message: InlineEditor.Cancelled) -> None:
    """Handle editor cancellation."""
    context = message.context
    if "post_id" in context:
        for block in self.query(PostBlock):
            if block.post.id == context["post_id"]:
                block.show_comment_editor = False
                block.refresh(recompose=True)
                break

async def _refresh_post(self, post_id: str) -> None:
    """Refresh a single post."""
    try:
        full_post = await self.app.api.get_post(post_id)
        if full_post:
            for block in self.query(PostBlock):
                if block.post.id == post_id:
                    block.post = full_post
                    block.show_comment_editor = False
                    block.refresh(recompose=True)
                    break
    except Exception as e:
        self.notify(f"Failed to refresh: {e}", severity="error")
```

**Step 5: Commit**

```bash
git add freefood/widgets/post.py freefood/screens/feed.py
git commit -m "feat: add comment creation

- Comment button shows inline editor
- Submit creates comment via API
- Post refreshes to show new comment"
```

---

## Task 18: Edit/Delete Posts

**Files:**
- Modify: `freefood/widgets/post.py`
- Modify: `freefood/screens/feed.py`

**Step 1: Add edit/delete messages**

```python
class EditRequested(Message):
    """Request to edit post."""
    def __init__(self, post: Post) -> None:
        self.post = post
        super().__init__()

class DeleteRequested(Message):
    """Request to delete post."""
    def __init__(self, post: Post) -> None:
        self.post = post
        super().__init__()
```

**Step 2: Handle edit/delete buttons**

```python
# In on_button_pressed:
elif event.button.id == "btn-edit":
    self.post_message(self.EditRequested(self.post))
elif event.button.id == "btn-delete":
    self.post_message(self.DeleteRequested(self.post))
```

**Step 3: Add edit state to PostBlock**

```python
self.editing = False

# In compose, before body:
if self.editing:
    yield InlineEditor(
        initial_text=self.post.body,
        context={"post_id": self.post.id, "editing": True},
        submit_label="Save"
    )
else:
    yield Static(self._format_body(), classes="post-body")
    # ... rest of body rendering
```

**Step 4: Handle edit in FeedScreen**

```python
def on_post_block_edit_requested(self, message: PostBlock.EditRequested) -> None:
    """Show editor for post."""
    for block in self.query(PostBlock):
        if block.post.id == message.post.id:
            block.editing = True
            block.refresh(recompose=True)
            break

# Update on_inline_editor_submitted to handle edits:
if "editing" in context:
    # Edit post
    try:
        await self.app.api.update_post(context["post_id"], message.text)
        self.notify("Post updated!")
        await self._refresh_post(context["post_id"])
    except Exception as e:
        self.notify(f"Failed: {e}", severity="error")
```

**Step 5: Handle delete with confirmation**

```python
async def on_post_block_delete_requested(self, message: PostBlock.DeleteRequested) -> None:
    """Delete post after confirmation."""
    # Simple confirmation via notify - could use modal in future
    post = message.post
    try:
        await self.app.api.delete_post(post.id)
        self.notify("Post deleted")
        # Remove from UI
        for block in self.query(PostBlock):
            if block.post.id == post.id:
                block.remove()
                break
    except Exception as e:
        self.notify(f"Failed: {e}", severity="error")
```

**Step 6: Commit**

```bash
git add freefood/widgets/post.py freefood/screens/feed.py
git commit -m "feat: add edit and delete for own posts

- Edit button shows inline editor with current text
- Delete button removes post
- Only shown on own posts"
```

---

## Task 19: Edit/Delete Comments

**Files:**
- Modify: `freefood/widgets/post.py`
- Modify: `freefood/screens/feed.py`

**Step 1: Update comment rendering with edit/delete buttons**

Update `_render_comment` to include buttons for own comments:
```python
def _render_comment(self, comment: Comment) -> Widget:
    """Render a single comment."""
    # Check if editing this comment
    if self.editing_comment_id == comment.id:
        return InlineEditor(
            initial_text=comment.body,
            context={"post_id": self.post.id, "comment_id": comment.id},
            submit_label="Save"
        )

    lines = comment.body.split("\n")
    if len(lines) > self.MAX_COMMENT_LINES:
        body = "\n".join(lines[: self.MAX_COMMENT_LINES]) + "\n[show more...]"
    else:
        body = comment.body

    author_name = comment.author.username if comment.author else "unknown"
    likes_str = f"[{comment.likes}♥]"

    with Horizontal(classes="comment"):
        yield Static(f"{likes_str} {body} -- @{author_name}")
        if comment.is_own:
            yield Button("Edit", id=f"edit-comment-{comment.id}", classes="comment-btn")
            yield Button("Del", id=f"del-comment-{comment.id}", classes="comment-btn")
```

**Step 2: Add comment editing state**

```python
self.editing_comment_id: str | None = None
```

**Step 3: Handle comment edit/delete buttons**

```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    button_id = event.button.id or ""

    if button_id.startswith("edit-comment-"):
        comment_id = button_id.replace("edit-comment-", "")
        self.editing_comment_id = comment_id
        self.refresh(recompose=True)
    elif button_id.startswith("del-comment-"):
        comment_id = button_id.replace("del-comment-", "")
        self.post_message(self.DeleteCommentRequested(self.post, comment_id))
    # ... rest of button handling
```

**Step 4: Add comment action messages**

```python
class DeleteCommentRequested(Message):
    """Request to delete comment."""
    def __init__(self, post: Post, comment_id: str) -> None:
        self.post = post
        self.comment_id = comment_id
        super().__init__()
```

**Step 5: Handle in FeedScreen**

```python
# In on_inline_editor_submitted, add comment edit handling:
elif "comment_id" in context:
    # Edit comment
    try:
        await self.app.api.update_comment(context["comment_id"], message.text)
        self.notify("Comment updated!")
        await self._refresh_post(context["post_id"])
    except Exception as e:
        self.notify(f"Failed: {e}", severity="error")

async def on_post_block_delete_comment_requested(self, message: PostBlock.DeleteCommentRequested) -> None:
    """Delete a comment."""
    try:
        await self.app.api.delete_comment(message.comment_id)
        self.notify("Comment deleted")
        await self._refresh_post(message.post.id)
    except Exception as e:
        self.notify(f"Failed: {e}", severity="error")
```

**Step 6: Commit**

```bash
git add freefood/widgets/post.py freefood/screens/feed.py
git commit -m "feat: add edit and delete for own comments

- Edit/Delete buttons on own comments
- Inline editor for comment editing
- Refresh post after changes"
```

---

## Task 20: User/Group Feed Navigation

**Files:**
- Modify: `freefood/widgets/post.py`
- Modify: `freefood/screens/feed.py`
- Modify: `freefood/api.py` (if needed)

**Step 1: Make usernames clickable**

Update header rendering to use clickable buttons:
```python
def _format_header(self) -> ComposeResult:
    """Format post header with clickable usernames."""
    author = self.post.author
    if author:
        yield Button(f"@{author.username}", id=f"user-{author.username}", classes="username-link")
        yield Static(" wrote", classes="post-header-text")
    else:
        yield Static("@unknown wrote", classes="post-header-text")

    if self.post.groups:
        yield Static(" in ", classes="post-header-text")
        for i, group in enumerate(self.post.groups):
            if i > 0:
                yield Static(", ", classes="post-header-text")
            yield Button(f"@{group.username}", id=f"group-{group.username}", classes="username-link")
        yield Static(":", classes="post-header-text")
    else:
        yield Static(":", classes="post-header-text")
```

**Step 2: Add CSS for username links**

```css
PostBlock .username-link {
    background: transparent;
    color: $accent;
    min-width: 0;
    padding: 0;
    border: none;
}

PostBlock .username-link:hover {
    text-style: underline;
}
```

**Step 3: Add navigation message**

```python
class NavigateToUser(Message):
    """Request to navigate to user/group feed."""
    def __init__(self, username: str, is_group: bool = False) -> None:
        self.username = username
        self.is_group = is_group
        super().__init__()
```

**Step 4: Handle username clicks**

```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    button_id = event.button.id or ""

    if button_id.startswith("user-"):
        username = button_id.replace("user-", "")
        self.post_message(self.NavigateToUser(username, is_group=False))
    elif button_id.startswith("group-"):
        username = button_id.replace("group-", "")
        self.post_message(self.NavigateToUser(username, is_group=True))
    # ... rest
```

**Step 5: Handle navigation in FeedScreen**

```python
def on_post_block_navigate_to_user(self, message: PostBlock.NavigateToUser) -> None:
    """Navigate to user or group feed."""
    view = View.GROUP_FEED if message.is_group else View.USER_FEED
    self.state.navigate_to(view, target=message.username)
    menu = self.query_one(MenuBar)
    menu.set_view(view)
    self.run_worker(self.refresh_content())
```

**Step 6: Update refresh_content to handle USER_FEED/GROUP_FEED**

```python
async def refresh_content(self) -> None:
    # ... existing code ...

    if self.state.current_view == View.HOME:
        self.posts = await api.get_home_feed()
    elif self.state.current_view == View.DIRECTS:
        self.posts = await api.get_directs()
    elif self.state.current_view in (View.USER_FEED, View.GROUP_FEED):
        self.posts = await api.get_user_feed(self.state.current_target)
    else:
        self.posts = []
```

**Step 7: Commit**

```bash
git add freefood/widgets/post.py freefood/screens/feed.py
git commit -m "feat: add user/group feed navigation

- Clickable usernames in post headers
- Navigate to user or group feed
- Pushed to history stack for back navigation"
```

---

## Task 21: Search View

**Files:**
- Modify: `freefood/screens/feed.py`
- Create: `freefood/widgets/search.py`
- Modify: `freefood/widgets/__init__.py`

**Step 1: Create search input widget**

Create `freefood/widgets/search.py`:
```python
"""Search input widget."""

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input


class SearchInput(Widget):
    """Search input with submit on Enter."""

    DEFAULT_CSS = """
    SearchInput {
        height: 3;
        margin: 0 0 1 0;
    }

    SearchInput Input {
        width: 100%;
    }
    """

    class Submitted(Message):
        """Search query submitted."""
        def __init__(self, query: str) -> None:
            self.query = query
            super().__init__()

    def __init__(self, initial_query: str = "") -> None:
        super().__init__()
        self.initial_query = initial_query

    def compose(self) -> ComposeResult:
        yield Input(
            placeholder="Search...",
            id="search-input",
            value=self.initial_query
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter in search input."""
        query = event.value.strip()
        if query:
            self.post_message(self.Submitted(query))
```

**Step 2: Update widgets init**

```python
from .search import SearchInput

__all__ = ["MenuBar", "PostBlock", "ComposeBlock", "InlineEditor", "SearchInput"]
```

**Step 3: Add search input to FeedScreen**

```python
def compose(self) -> ComposeResult:
    yield MenuBar(self.state.current_view)
    with ScrollableContainer(id="feed-container"):
        if self.state.current_view == View.SEARCH:
            yield SearchInput(self.state.search_query)
        elif self.state.current_view in (View.HOME, View.DIRECTS):
            yield ComposeBlock()
        yield Static("Loading feed...", classes="loading")
```

**Step 4: Handle search submission**

```python
async def on_search_input_submitted(self, message: SearchInput.Submitted) -> None:
    """Handle search query."""
    self.state.search_query = message.query
    self.run_worker(self.refresh_content())
```

**Step 5: Update refresh_content for search**

```python
elif self.state.current_view == View.SEARCH:
    if self.state.search_query:
        self.posts = await api.search(self.state.search_query)
    else:
        self.posts = []
```

**Step 6: Show empty state for search**

```python
if not self.posts:
    if self.state.current_view == View.SEARCH and not self.state.search_query:
        container.mount(Static("Enter a search query above", classes="loading"))
    else:
        container.mount(Static("No posts found", classes="loading"))
```

**Step 7: Commit**

```bash
git add freefood/widgets/search.py freefood/widgets/__init__.py freefood/screens/feed.py
git commit -m "feat: add search view

- SearchInput widget with Enter to submit
- Query persisted in state
- Results displayed as posts"
```

---

## Task 22: Notifications Screen

**Files:**
- Create: `freefood/widgets/notification.py`
- Modify: `freefood/widgets/__init__.py`
- Modify: `freefood/screens/feed.py`
- Modify: `freefood/api.py`
- Modify: `freefood/models.py`

**Step 1: Add Notification model**

Add to `freefood/models.py`:
```python
@dataclass
class Notification:
    """A notification event."""

    id: str
    event_type: str  # "mention_in_post", "mention_in_comment", "subscription_request", etc.
    created_at: datetime
    created_by: User | None
    post_id: str | None = None
    comment_id: str | None = None
    post_body: str | None = None
    comment_body: str | None = None
```

**Step 2: Add get_notifications to API**

Add to `freefood/api.py`:
```python
async def get_notifications(self, offset: int = 0, limit: int = 30) -> list[Notification]:
    """Fetch notifications."""
    client = await self._get_client()
    response = await client.get(
        "/v2/notifications", params={"offset": offset, "limit": limit}
    )
    response.raise_for_status()
    return self._parse_notifications(response.json())

def _parse_notifications(self, data: dict) -> list[Notification]:
    """Parse notifications from API response."""
    users_by_id = {u["id"]: self._parse_user(u) for u in data.get("users", [])}
    posts_by_id = {p["id"]: p for p in data.get("posts", [])}
    comments_by_id = {c["id"]: c for c in data.get("comments", [])}

    notifications = []
    for n in data.get("notifications", []):
        post_id = n.get("postId")
        comment_id = n.get("commentId")

        post_body = None
        if post_id and post_id in posts_by_id:
            post_body = posts_by_id[post_id].get("body", "")[:100]

        comment_body = None
        if comment_id and comment_id in comments_by_id:
            comment_body = comments_by_id[comment_id].get("body", "")[:100]

        notifications.append(Notification(
            id=n["id"],
            event_type=n.get("eventType", "unknown"),
            created_at=datetime.fromtimestamp(int(n["createdAt"]) / 1000),
            created_by=users_by_id.get(n.get("createdBy")),
            post_id=post_id,
            comment_id=comment_id,
            post_body=post_body,
            comment_body=comment_body,
        ))
    return notifications
```

**Step 3: Create NotificationBlock widget**

Create `freefood/widgets/notification.py`:
```python
"""Notification block widget."""

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, Button

from freefood.models import Notification
from freefood.widgets.post import format_time_ago


class NotificationBlock(Widget, can_focus=True):
    """Widget displaying a notification."""

    DEFAULT_CSS = """
    NotificationBlock {
        height: auto;
        border: solid $primary;
        padding: 1;
        margin: 1 0;
    }

    NotificationBlock:focus {
        border: solid $accent;
    }

    NotificationBlock .notification-text {
        margin-bottom: 1;
    }

    NotificationBlock .notification-meta {
        color: $text-muted;
    }
    """

    class NavigateToPost(Message):
        """Request to navigate to post."""
        def __init__(self, post_id: str) -> None:
            self.post_id = post_id
            super().__init__()

    class NavigateToUser(Message):
        """Request to navigate to user."""
        def __init__(self, username: str) -> None:
            self.username = username
            super().__init__()

    def __init__(self, notification: Notification) -> None:
        super().__init__()
        self.notification = notification

    def compose(self) -> ComposeResult:
        n = self.notification
        author = n.created_by

        # Format based on event type
        if n.event_type == "mention_in_post":
            text = f"mentioned you in a post"
            if n.post_body:
                text += f": {n.post_body}..."
        elif n.event_type == "mention_in_comment":
            text = f"mentioned you in a comment"
            if n.comment_body:
                text += f": {n.comment_body}..."
        elif n.event_type == "direct_message":
            text = "sent you a direct message"
        elif n.event_type == "subscription_request":
            text = "wants to subscribe to you"
        elif n.event_type == "subscription_approved":
            text = "approved your subscription request"
        else:
            text = n.event_type

        if author:
            yield Button(f"@{author.username}", id=f"user-{author.username}", classes="username-link")
            yield Static(f" {text}", classes="notification-text")
        else:
            yield Static(text, classes="notification-text")

        yield Static(format_time_ago(n.created_at), classes="notification-meta")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id.startswith("user-"):
            username = button_id.replace("user-", "")
            self.post_message(self.NavigateToUser(username))
```

**Step 4: Update widgets init**

```python
from .notification import NotificationBlock

__all__ = ["MenuBar", "PostBlock", "ComposeBlock", "InlineEditor", "SearchInput", "NotificationBlock"]
```

**Step 5: Update FeedScreen for notifications**

```python
from freefood.widgets.notification import NotificationBlock
from freefood.models import Notification

# Add to class:
self.notifications: list[Notification] = []

# In refresh_content:
elif self.state.current_view == View.NOTIFICATIONS:
    self.notifications = await api.get_notifications()
    self.posts = []  # Clear posts

# In rendering section:
if self.state.current_view == View.NOTIFICATIONS:
    if not self.notifications:
        container.mount(Static("No notifications", classes="loading"))
    else:
        for n in self.notifications:
            container.mount(NotificationBlock(n))
elif not self.posts:
    # ... existing empty state handling
```

**Step 6: Commit**

```bash
git add freefood/models.py freefood/api.py freefood/widgets/notification.py freefood/widgets/__init__.py freefood/screens/feed.py
git commit -m "feat: add notifications view

- Notification model and API method
- NotificationBlock widget with event formatting
- Clickable usernames in notifications"
```

---

## Task 23: Polish & Error Handling

**Files:**
- Various files for cleanup

**Step 1: Review and fix edge cases**

Check for:
- Empty username handling
- Network timeout handling
- Very long post bodies
- Unicode/emoji in content

**Step 2: Improve error messages**

Replace generic "Failed" messages with specific ones:
- "Network error: could not connect"
- "Post not found"
- "You don't have permission to..."

**Step 3: Add loading indicators**

Replace "Loading..." text with animated spinner where appropriate.

**Step 4: Test on all platforms**

- Linux: Full test
- macOS: Full test
- Windows: Full test (check path separators, terminal compatibility)

**Step 5: Final cleanup**

- Remove debug print statements
- Remove unused imports
- Add missing docstrings
- Run linter

**Step 6: Commit**

```bash
git add -A
git commit -m "chore: polish and error handling

- Improved error messages
- Edge case handling
- Cross-platform testing complete"
```

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
