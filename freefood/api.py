"""FreeFeed API client."""

from datetime import datetime

import httpx

from .models import Comment, Post, User, Notification


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

    async def validate_token(self) -> User:
        """Validate token and return current user."""
        client = await self._get_client()
        response = await client.get("/v4/users/whoami")
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
        users_by_id = {u["id"]: self._parse_user(u) for u in data.get("users", [])}
        for group in data.get("groups", []):
            users_by_id[group["id"]] = self._parse_user(group)
        comments_by_id = {
            c["id"]: self._parse_comment(c, users_by_id)
            for c in data.get("comments", [])
        }

        # Handle both list (timelines) and dict (single post) response formats
        posts_data = data.get("posts", [])
        if isinstance(posts_data, dict):
            posts_data = [posts_data]

        posts = []
        for p in posts_data:
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
                    omitted_comments_offset=p.get("omittedCommentsOffset", 0),
                    omitted_comment_likes=p.get("omittedCommentLikes", 0),
                    omitted_likes=p.get("omittedLikes", 0),
                    likes=post_likes,
                    is_liked=p.get("hasOwnLike", False),
                    is_hidden=p.get("isHidden", False),
                    is_own=is_own,
                )
            )
        return posts

    async def get_home_feed(self, offset: int = 0, limit: int = 30) -> list[Post]:
        """Fetch home timeline."""
        client = await self._get_client()
        response = await client.get(
            "/v4/timelines/home", params={"offset": offset, "limit": limit}
        )
        response.raise_for_status()
        return self._denormalize_posts(response.json())

    async def get_user_feed(
        self, username: str, offset: int = 0, limit: int = 30
    ) -> list[Post]:
        """Fetch user timeline."""
        client = await self._get_client()
        response = await client.get(
            f"/v4/timelines/{username}", params={"offset": offset, "limit": limit}
        )
        response.raise_for_status()
        return self._denormalize_posts(response.json())

    async def get_user_subscription_status(self, username: str) -> bool:
        """Return whether current user is subscribed to the given user."""
        client = await self._get_client()
        response = await client.get(f"/v4/users/{username}")
        response.raise_for_status()
        data = response.json()

        for key in ("youAreSubscribed", "youSubscribed", "isSubscribed", "subscribed"):
            if key in data:
                return bool(data[key])

        user_data = data.get("users")
        if isinstance(user_data, dict):
            for key in ("youAreSubscribed", "youSubscribed", "isSubscribed", "subscribed"):
                if key in user_data:
                    return bool(user_data[key])
            you_can = user_data.get("youCan")
            if isinstance(you_can, list) and "unsubscribe" in you_can:
                return True

        return False

    async def get_directs(self, offset: int = 0, limit: int = 30) -> list[Post]:
        """Fetch direct messages."""
        client = await self._get_client()
        response = await client.get(
            "/v4/timelines/filter/directs", params={"offset": offset, "limit": limit}
        )
        response.raise_for_status()
        return self._denormalize_posts(response.json())

    async def get_notifications(
        self, offset: int = 0, limit: int = 30
    ) -> list[Notification]:
        """Fetch notifications."""
        client = await self._get_client()
        response = await client.get(
            "/v4/notifications", params={"offset": offset, "limit": limit}
        )
        response.raise_for_status()
        data = response.json()

        users_by_id = {u["id"]: self._parse_user(u) for u in data.get("users", [])}
        notifications = []
        for item in data.get("Notifications", []):
            created_user_id = item.get("created_user_id", item.get("createdBy"))
            created_user = users_by_id.get(created_user_id)
            if "date" in item and item["date"]:
                created_at = datetime.fromisoformat(item["date"].replace("Z", "+00:00"))
            else:
                created_at = datetime.fromtimestamp(int(item.get("createdAt", "0")) / 1000)
            notifications.append(
                Notification(
                    id=item.get("id", ""),
                    event_id=item.get("eventId", item.get("event_id", "")),
                    event_type=item.get("eventType", item.get("event_type", "")),
                    date=created_at,
                    created_user=created_user,
                    post_id=item.get(
                        "postId", item.get("post_id", item.get("target_post_id"))
                    ),
                    comment_id=item.get(
                        "commentId", item.get("comment_id", item.get("target_comment_id"))
                    ),
                )
            )
        return notifications

    async def get_unread_notifications_count(self) -> int:
        """Fetch unread notifications count."""
        client = await self._get_client()
        response = await client.get("/v4/users/whoami")
        response.raise_for_status()
        data = response.json()
        return int(data.get("unreadNotificationsNumber", 0))

    async def search(self, query: str, offset: int = 0, limit: int = 30) -> list[Post]:
        """Search posts."""
        client = await self._get_client()
        response = await client.get(
            "/v4/search", params={"q": query, "offset": offset, "limit": limit}
        )
        response.raise_for_status()
        return self._denormalize_posts(response.json())

    async def get_post(self, post_id: str) -> Post | None:
        """Fetch single post with all comments."""
        client = await self._get_client()
        response = await client.get(
            f"/v4/posts/{post_id}", params={"maxComments": "all", "maxLikes": "all"}
        )
        response.raise_for_status()
        posts = self._denormalize_posts(response.json())
        return posts[0] if posts else None

    # Post actions
    async def like_post(self, post_id: str) -> None:
        """Like a post."""
        client = await self._get_client()
        response = await client.post(f"/v4/posts/{post_id}/like")
        response.raise_for_status()

    async def unlike_post(self, post_id: str) -> None:
        """Unlike a post."""
        client = await self._get_client()
        response = await client.post(f"/v4/posts/{post_id}/unlike")
        response.raise_for_status()

    async def hide_post(self, post_id: str) -> None:
        """Hide a post."""
        client = await self._get_client()
        response = await client.post(f"/v4/posts/{post_id}/hide")
        response.raise_for_status()

    async def unhide_post(self, post_id: str) -> None:
        """Unhide a post."""
        client = await self._get_client()
        response = await client.post(f"/v4/posts/{post_id}/unhide")
        response.raise_for_status()

    async def create_post(self, body: str, feeds: list[str]) -> Post:
        """Create a new post."""
        client = await self._get_client()
        response = await client.post(
            "/v4/posts", json={"post": {"body": body}, "meta": {"feeds": feeds}}
        )
        response.raise_for_status()
        posts = self._denormalize_posts(response.json())
        return posts[0]

    async def subscribe(self, username: str) -> None:
        """Subscribe to a user."""
        client = await self._get_client()
        response = await client.post(f"/v4/users/{username}/subscribe")
        response.raise_for_status()

    async def unsubscribe(self, username: str) -> None:
        """Unsubscribe from a user."""
        client = await self._get_client()
        response = await client.post(f"/v4/users/{username}/unsubscribe")
        response.raise_for_status()

    async def update_post(self, post_id: str, body: str) -> Post:
        """Update a post."""
        client = await self._get_client()
        response = await client.put(
            f"/v4/posts/{post_id}", json={"post": {"body": body}}
        )
        response.raise_for_status()
        posts = self._denormalize_posts(response.json())
        return posts[0]

    async def delete_post(self, post_id: str) -> None:
        """Delete a post."""
        client = await self._get_client()
        response = await client.delete(f"/v4/posts/{post_id}")
        response.raise_for_status()

    # Comment actions
    async def create_comment(self, post_id: str, body: str) -> Comment:
        """Create a comment on a post."""
        client = await self._get_client()
        response = await client.post(
            "/v4/comments", json={"comment": {"body": body, "postId": post_id}}
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
            f"/v4/comments/{comment_id}", json={"comment": {"body": body}}
        )
        response.raise_for_status()

    async def delete_comment(self, comment_id: str) -> None:
        """Delete a comment."""
        client = await self._get_client()
        response = await client.delete(f"/v4/comments/{comment_id}")
        response.raise_for_status()

    async def like_comment(self, comment_id: str) -> None:
        """Like a comment."""
        client = await self._get_client()
        response = await client.post(f"/v4/comments/{comment_id}/like")
        response.raise_for_status()

    async def unlike_comment(self, comment_id: str) -> None:
        """Unlike a comment."""
        client = await self._get_client()
        response = await client.post(f"/v4/comments/{comment_id}/unlike")
        response.raise_for_status()

    # Subscription actions
    async def subscribe(self, username: str) -> None:
        """Subscribe to a user."""
        client = await self._get_client()
        response = await client.post(f"/v4/users/{username}/subscribe")
        response.raise_for_status()

    async def unsubscribe(self, username: str) -> None:
        """Unsubscribe from a user."""
        client = await self._get_client()
        response = await client.post(f"/v4/users/{username}/unsubscribe")
        response.raise_for_status()
