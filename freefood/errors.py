"""Custom exceptions for FreeFood."""


class FreeFeedError(Exception):
    """Base exception for FreeFood."""


class ApiError(FreeFeedError):
    """API returned an error."""


class AuthError(FreeFeedError):
    """Authentication failed."""


class NetworkError(FreeFeedError):
    """Network connection failed."""
