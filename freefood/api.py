"""FreeFeed API client."""

import httpx

from freefood.errors import ApiError, AuthError, NetworkError
from freefood.models import Comment, Notification, Post, User
from freefood.parsers import ResponseParser


class FreeFeedAPI:
    """Async client for FreeFeed API."""

    DEFAULT_BASE_URL = "https://freefeed.net"

    def __init__(self, token: str, base_url: str | None = None) -> None:
        """Initialize API client with auth token and optional base URL."""
        self.token = token
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.current_user: User | None = None
        self._client: httpx.AsyncClient | None = None
        self._parser = ResponseParser(self.base_url)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make an HTTP request with error handling."""
        try:
            client = await self._get_client()
            response = await client.request(method, path, **kwargs)
            response.raise_for_status()
            return response
        except httpx.NetworkError as e:
            raise NetworkError(f"Network error: {e}") from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                raise AuthError(
                    f"Auth error: {e.response.status_code} {e.response.text}"
                ) from e
            raise ApiError(
                f"API error: {e.response.status_code} {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise NetworkError(f"Request error: {e}") from e

    async def validate_token(self) -> User:
        """Validate token and return current user."""
        response = await self._request("GET", "/v4/users/whoami")
        data = response.json()
        self.current_user = self._parser.parse_user(data["users"])
        return self.current_user

    async def get_home_feed(self, offset: int = 0, limit: int = 30) -> list[Post]:
        """Fetch home timeline."""
        response = await self._request(
            "GET", "/v4/timelines/home", params={"offset": offset, "limit": limit}
        )
        return self._parser.denormalize_posts(response.json(), self.current_user)

    async def get_user_feed(
        self, username: str, offset: int = 0, limit: int = 30
    ) -> list[Post]:
        """Fetch user timeline."""
        response = await self._request(
            "GET",
            f"/v4/timelines/{username}",
            params={"offset": offset, "limit": limit},
        )
        return self._parser.denormalize_posts(response.json(), self.current_user)

    async def get_user_subscription_status(self, username: str) -> bool:
        """Return whether current user is subscribed to the given user."""
        response = await self._request("GET", f"/v4/users/{username}")
        data = response.json()

        for key in ("youAreSubscribed", "youSubscribed", "isSubscribed", "subscribed"):
            if key in data:
                return bool(data[key])

        user_data = data.get("users")
        if isinstance(user_data, dict):
            for key in (
                "youAreSubscribed",
                "youSubscribed",
                "isSubscribed",
                "subscribed",
            ):
                if key in user_data:
                    return bool(user_data[key])
            you_can = user_data.get("youCan")
            if isinstance(you_can, list) and "unsubscribe" in you_can:
                return True

        return False

    async def get_directs(self, offset: int = 0, limit: int = 30) -> list[Post]:
        """Fetch direct messages."""
        response = await self._request(
            "GET",
            "/v4/timelines/filter/directs",
            params={"offset": offset, "limit": limit},
        )
        return self._parser.denormalize_posts(response.json(), self.current_user)

    async def get_notifications(
        self, offset: int = 0, limit: int = 30
    ) -> list[Notification]:
        """Fetch notifications."""
        response = await self._request(
            "GET", "/v4/notifications", params={"offset": offset, "limit": limit}
        )
        return self._parser.parse_notifications(response.json())

    async def get_unread_notifications_count(self) -> int:
        """Fetch unread notifications count."""
        response = await self._request("GET", "/v4/users/whoami")
        data = response.json()
        return int(data.get("unreadNotificationsNumber", 0))

    async def get_unread_directs_count(self) -> int:
        """Fetch unread directs count."""
        response = await self._request("GET", "/v4/users/whoami")
        data = response.json()
        return int(data.get("unreadDirectsNumber", 0))

    async def search(self, query: str, offset: int = 0, limit: int = 30) -> list[Post]:
        """Search posts."""
        response = await self._request(
            "GET", "/v4/search", params={"q": query, "offset": offset, "limit": limit}
        )
        return self._parser.denormalize_posts(response.json(), self.current_user)

    async def get_post(self, post_id: str) -> Post | None:
        """Fetch single post with all comments."""
        response = await self._request(
            "GET",
            f"/v4/posts/{post_id}",
            params={"maxComments": "all", "maxLikes": "all"},
        )
        posts = self._parser.denormalize_posts(response.json(), self.current_user)
        return posts[0] if posts else None

    # Post actions
    async def like_post(self, post_id: str) -> None:
        """Like a post."""
        await self._request("POST", f"/v4/posts/{post_id}/like")

    async def unlike_post(self, post_id: str) -> None:
        """Unlike a post."""
        await self._request("POST", f"/v4/posts/{post_id}/unlike")

    async def hide_post(self, post_id: str) -> None:
        """Hide a post."""
        await self._request("POST", f"/v4/posts/{post_id}/hide")

    async def unhide_post(self, post_id: str) -> None:
        """Unhide a post."""
        await self._request("POST", f"/v4/posts/{post_id}/unhide")

    async def create_post(self, body: str, feeds: list[str]) -> Post:
        """Create a new post."""
        response = await self._request(
            "POST",
            "/v4/posts",
            json={"post": {"body": body}, "meta": {"feeds": feeds}},
        )
        posts = self._parser.denormalize_posts(response.json(), self.current_user)
        return posts[0]

    async def subscribe(self, username: str) -> None:
        """Subscribe to a user."""
        await self._request("POST", f"/v4/users/{username}/subscribe")

    async def unsubscribe(self, username: str) -> None:
        """Unsubscribe from a user."""
        await self._request("POST", f"/v4/users/{username}/unsubscribe")

    async def update_post(self, post_id: str, body: str) -> Post:
        """Update a post."""
        response = await self._request(
            "PUT", f"/v4/posts/{post_id}", json={"post": {"body": body}}
        )
        posts = self._parser.denormalize_posts(response.json(), self.current_user)
        return posts[0]

    async def delete_post(self, post_id: str) -> None:
        """Delete a post."""
        await self._request("DELETE", f"/v4/posts/{post_id}")

    # Comment actions
    async def create_comment(self, post_id: str, body: str) -> Comment:
        """Create a comment on a post."""
        response = await self._request(
            "POST",
            "/v4/comments",
            json={"comment": {"body": body, "postId": post_id}},
        )
        data = response.json()
        users_by_id = {
            u["id"]: self._parser.parse_user(u) for u in data.get("users", [])
        }
        return self._parser.parse_comment(
            data["comments"], users_by_id, self.current_user
        )

    async def update_comment(self, comment_id: str, body: str) -> None:
        """Update a comment."""
        await self._request(
            "PUT", f"/v4/comments/{comment_id}", json={"comment": {"body": body}}
        )

    async def delete_comment(self, comment_id: str) -> None:
        """Delete a comment."""
        await self._request("DELETE", f"/v4/comments/{comment_id}")

    async def like_comment(self, comment_id: str) -> None:
        """Like a comment."""
        await self._request("POST", f"/v4/comments/{comment_id}/like")

    async def unlike_comment(self, comment_id: str) -> None:
        """Unlike a comment."""
        await self._request("POST", f"/v4/comments/{comment_id}/unlike")
