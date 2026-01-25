"""FreeFeed API client."""

from datetime import datetime

import httpx

from .models import Comment, Post, User


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

    async def get_home_feed(self, offset: int = 0, limit: int = 30) -> list[Post]:
        """Fetch home timeline."""
        client = await self._get_client()
        response = await client.get(
            "/v2/timelines/home", params={"offset": offset, "limit": limit}
        )
        response.raise_for_status()
        return self._denormalize_posts(response.json())

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
