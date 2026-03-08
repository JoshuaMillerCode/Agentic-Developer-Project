"""
Minimal TMDb API client for discovery and configuration.
Used by the backend to serve discovery sections and image base URLs without invoking the agent.
Uses TMDB_API_KEY from environment (same as MCP server).

Unlike the MCP server's tmdb_tools, this module returns raw Python dicts from _request (not JSON strings),
so routes can build response payloads directly.
"""

import os
from typing import Any

import httpx

TMDB_BASE = "https://api.themoviedb.org/3"
HTTP_TIMEOUT_SECONDS = 30


class TmdbClientError(Exception):
    """Raised when a TMDb API or network request fails. Message is safe to log (no secrets)."""


def _get_api_key() -> str:
    key = os.environ.get("TMDB_API_KEY")
    if not key or not key.strip():
        raise RuntimeError("TMDB_API_KEY is not set.")
    return key.strip()


def _request(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Call TMDb API; returns raw dict (not JSON string). Raises TmdbClientError on HTTP/network errors."""
    key = _get_api_key()
    url = f"{TMDB_BASE}{path}"
    q = dict(params) if params else {}
    q.setdefault("api_key", key)
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as client:
            r = client.get(url, params=q)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise TmdbClientError("TMDb rate limit exceeded") from e
        raise TmdbClientError(f"TMDb API error: {e.response.status_code}") from e
    except (httpx.RequestError, httpx.TimeoutException) as e:
        raise TmdbClientError("TMDb request failed") from e


def get_configuration() -> dict[str, Any]:
    """Return TMDb API configuration (image base URLs, etc.)."""
    return _request("/configuration")


def get_movie_popular(page: int = 1, language: str = "en-US") -> dict[str, Any]:
    """Popular movies list."""
    return _request("/movie/popular", {"page": page, "language": language})


def get_movie_now_playing(page: int = 1, language: str = "en-US") -> dict[str, Any]:
    """Movies now playing in theatres."""
    return _request("/movie/now_playing", {"page": page, "language": language})


def get_tv_popular(page: int = 1, language: str = "en-US") -> dict[str, Any]:
    """Popular TV shows list."""
    return _request("/tv/popular", {"page": page, "language": language})


def get_trending_people(time_window: str = "day", page: int = 1) -> dict[str, Any]:
    """Trending people (actors, etc.). time_window: 'day' or 'week'."""
    tw = (time_window or "day").strip().lower()
    if tw not in ("day", "week"):
        tw = "day"
    return _request(f"/trending/person/{tw}", {"page": page})
