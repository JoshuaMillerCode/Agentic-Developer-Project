"""
TMDB API tools for the MCP server.
Exposes core movie/TV operations as callable tools.
"""

import json
import os

import httpx

TMDB_BASE = "https://api.themoviedb.org/3"
MAX_PAGE = 500
MAX_QUERY_LENGTH = 500
HTTP_TIMEOUT_SECONDS = 30
MAX_LANGUAGE_LENGTH = 10
DISCOVER_SORT_OPTIONS = frozenset({
    "popularity.asc", "popularity.desc",
    "primary_release_date.asc", "primary_release_date.desc",
    "vote_average.asc", "vote_average.desc",
    "vote_count.asc", "vote_count.desc",
    "title.asc", "title.desc",
    "original_title.asc", "original_title.desc",
    "revenue.asc", "revenue.desc",
    "release_date.asc", "release_date.desc",
})


def _get_api_key() -> str:
    key = os.environ.get("TMDB_API_KEY")
    if not key or not key.strip():
        raise RuntimeError(
            "TMDB_API_KEY is not set. Copy .env.example to .env and add your key from https://www.themoviedb.org/settings/api"
        )
    return key.strip()


def _request(path: str, params: dict | None = None) -> dict:
    """Call TMDB API; auth via api_key query param. Returns JSON or raises."""
    key = _get_api_key()
    url = f"{TMDB_BASE}{path}"
    q = dict(params) if params else {}
    q.setdefault("api_key", key)
    with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as client:
        r = client.get(url, params=q)
        r.raise_for_status()
        return r.json()


def _call(path: str, params: dict | None = None) -> str:
    """Perform request and return JSON string; on error return safe JSON (no exception message leakage)."""
    try:
        data = _request(path, params)
        return json.dumps(data, indent=2)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return json.dumps({"error": "rate_limit_exceeded", "status_code": 429, "detail": "TMDB rate limit exceeded; retry with backoff."})
        return json.dumps({"error": "api_error", "status_code": e.response.status_code})
    except Exception:
        return json.dumps({"error": "request_failed", "detail": "The request could not be completed."})


def _validate_page(page: int) -> str | None:
    if page < 1:
        return "page must be >= 1"
    if page > MAX_PAGE:
        return f"page must be <= {MAX_PAGE}"
    return None


def _coerce_page(page: object) -> tuple[int | None, str | None]:
    """Coerce page to int; return (value, None) or (None, error_detail)."""
    try:
        p = int(page)
    except (TypeError, ValueError):
        return None, "page must be an integer"
    err = _validate_page(p)
    return (p, None) if err is None else (None, err)


def _validate_id(value: int, name: str) -> str | None:
    if value < 1:
        return f"{name} must be a positive integer"
    return None


def _coerce_id(value: object, name: str) -> tuple[int | None, str | None]:
    """Coerce ID to int; return (value, None) or (None, error_detail)."""
    try:
        v = int(value)
    except (TypeError, ValueError):
        return None, f"{name} must be an integer"
    err = _validate_id(v, name)
    return (v, None) if err is None else (None, err)


def get_configuration() -> str:
    """Get API configuration: image base URLs, languages, countries, timezones."""
    return _call("/configuration")


def search_movie(query: str, page: int = 1) -> str:
    """Search for movies by title."""
    query = (query or "").strip()
    if not query:
        return json.dumps({"error": "validation_error", "detail": "query must be non-empty"})
    if len(query) > MAX_QUERY_LENGTH:
        return json.dumps({"error": "validation_error", "detail": f"query must be at most {MAX_QUERY_LENGTH} characters"})
    p, err = _coerce_page(page)
    if err:
        return json.dumps({"error": "validation_error", "detail": err})
    return _call("/search/movie", {"query": query, "page": p})


def discover_movie(
    sort_by: str = "popularity.desc",
    page: int = 1,
    language: str = "en-US",
    primary_release_year: int | None = None,
    vote_average_gte: float | None = None,
    vote_average_lte: float | None = None,
    with_genres: str | None = None,
    year: int | None = None,
) -> str:
    """Discover movies with filters and sort. sort_by: popularity.desc, popularity.asc, primary_release_date.desc, vote_average.desc, vote_count.desc. with_genres: comma-separated genre IDs."""
    sort_by = (sort_by or "").strip().lower()
    if sort_by not in DISCOVER_SORT_OPTIONS:
        return json.dumps({
            "error": "validation_error",
            "detail": f"sort_by must be one of: {', '.join(sorted(DISCOVER_SORT_OPTIONS))}",
        })
    p, err = _coerce_page(page)
    if err:
        return json.dumps({"error": "validation_error", "detail": err})
    if primary_release_year is not None:
        try:
            primary_release_year = int(primary_release_year)
        except (TypeError, ValueError):
            return json.dumps({"error": "validation_error", "detail": "primary_release_year must be an integer"})
        if not (1900 <= primary_release_year <= 2100):
            return json.dumps({"error": "validation_error", "detail": "primary_release_year must be between 1900 and 2100"})
    if year is not None:
        try:
            year = int(year)
        except (TypeError, ValueError):
            return json.dumps({"error": "validation_error", "detail": "year must be an integer"})
        if not (1900 <= year <= 2100):
            return json.dumps({"error": "validation_error", "detail": "year must be between 1900 and 2100"})
    if vote_average_gte is not None:
        try:
            vote_average_gte = float(vote_average_gte)
        except (TypeError, ValueError):
            return json.dumps({"error": "validation_error", "detail": "vote_average_gte must be a number"})
        if not (0 <= vote_average_gte <= 10):
            return json.dumps({"error": "validation_error", "detail": "vote_average_gte must be between 0 and 10"})
    if vote_average_lte is not None:
        try:
            vote_average_lte = float(vote_average_lte)
        except (TypeError, ValueError):
            return json.dumps({"error": "validation_error", "detail": "vote_average_lte must be a number"})
        if not (0 <= vote_average_lte <= 10):
            return json.dumps({"error": "validation_error", "detail": "vote_average_lte must be between 0 and 10"})
    if vote_average_gte is not None and vote_average_lte is not None and vote_average_gte > vote_average_lte:
        return json.dumps({"error": "validation_error", "detail": "vote_average_gte must be less than or equal to vote_average_lte"})
    language = (language or "en-US").strip()
    if len(language) > MAX_LANGUAGE_LENGTH:
        return json.dumps({"error": "validation_error", "detail": f"language must be at most {MAX_LANGUAGE_LENGTH} characters"})
    if with_genres is not None and with_genres:
        parts = [p.strip() for p in with_genres.split(",") if p.strip()]
        if not all(p.isdigit() for p in parts):
            return json.dumps({"error": "validation_error", "detail": "with_genres must be comma-separated genre IDs (digits only)"})
    params = {
        "sort_by": sort_by,
        "page": p,
        "language": language,
        "include_adult": False,
        "include_video": False,
    }
    if primary_release_year is not None:
        params["primary_release_year"] = primary_release_year
    if vote_average_gte is not None:
        params["vote_average.gte"] = vote_average_gte
    if vote_average_lte is not None:
        params["vote_average.lte"] = vote_average_lte
    if with_genres:
        params["with_genres"] = with_genres
    if year is not None:
        params["year"] = year
    return _call("/discover/movie", params)


def search_tv(query: str, page: int = 1) -> str:
    """Search for TV shows by title."""
    query = (query or "").strip()
    if not query:
        return json.dumps({"error": "validation_error", "detail": "query must be non-empty"})
    if len(query) > MAX_QUERY_LENGTH:
        return json.dumps({"error": "validation_error", "detail": f"query must be at most {MAX_QUERY_LENGTH} characters"})
    p, err = _coerce_page(page)
    if err:
        return json.dumps({"error": "validation_error", "detail": err})
    return _call("/search/tv", {"query": query, "page": p})


def get_movie_details(movie_id: int) -> str:
    """Get details for a movie by its TMDB ID."""
    mid, err = _coerce_id(movie_id, "movie_id")
    if err:
        return json.dumps({"error": "validation_error", "detail": err})
    return _call(f"/movie/{mid}")


def get_tv_details(tv_id: int) -> str:
    """Get details for a TV show by its TMDB ID."""
    tid, err = _coerce_id(tv_id, "tv_id")
    if err:
        return json.dumps({"error": "validation_error", "detail": err})
    return _call(f"/tv/{tid}")


def get_trending_movies(time_window: str = "day") -> str:
    """Get trending movies (time_window: 'day' or 'week')."""
    time_window = (time_window or "day").strip().lower()
    if time_window not in ("day", "week"):
        return json.dumps({"error": "validation_error", "detail": "Use 'day' or 'week'"})
    return _call(f"/trending/movie/{time_window}")


def get_trending_tv(time_window: str = "day") -> str:
    """Get trending TV shows (time_window: 'day' or 'week')."""
    time_window = (time_window or "day").strip().lower()
    if time_window not in ("day", "week"):
        return json.dumps({"error": "validation_error", "detail": "Use 'day' or 'week'"})
    return _call(f"/trending/tv/{time_window}")
