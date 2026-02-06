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
class Attachment:
    """A file attachment on a post."""

    id: str
    file_name: str
    file_size: int
    media_type: str
    url: str
    thumbnail_url: str | None = None


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
    attachments: list[Attachment] = field(default_factory=list)
    direct_recipients: list[User] = field(default_factory=list)
    is_liked: bool = False
    is_hidden: bool = False
    is_own: bool = False


@dataclass
class Notification:
    """A notification event."""

    id: str
    event_id: str
    event_type: str
    date: datetime
    created_user: User | None
    post_id: str | None = None
    comment_id: str | None = None


class View(Enum):
    """Application view types."""

    HOME = "home"
    NOTIFICATIONS = "notifications"
    DIRECTS = "directs"
    SEARCH = "search"
    USER_FEED = "user_feed"
    GROUP_FEED = "group_feed"
    ERRORS = "errors"


@dataclass
class HistoryEntry:
    """Navigation history entry."""

    view: View
    target: str | None  # username/group for USER_FEED/GROUP_FEED
    scroll_position: int
    query: str | None = None  # for SEARCH
