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


@dataclass
class Comment:
    """A comment on a post."""

    id: str
    body: str
    author: User | None
    created_at: datetime
    likes: int
    is_liked: bool = False
    is_own: bool = False


@dataclass
class Post:
    """A FreeFeed post."""

    id: str
    body: str
    author: User | None
    groups: list[User]
    created_at: datetime
    updated_at: datetime
    comments: list[Comment]
    omitted_comments: int
    omitted_comments_offset: int
    omitted_comment_likes: int
    omitted_likes: int
    likes: list[User]
    is_liked: bool = False
    is_hidden: bool = False
    is_own: bool = False


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
