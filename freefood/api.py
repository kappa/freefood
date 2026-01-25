"""FreeFeed API client."""

import httpx

from .models import User


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
