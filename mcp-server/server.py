#!/usr/bin/env python3
"""
TMDB MCP Server — wraps The Movie Database API as MCP tools.

Run from project root with TMDB_API_KEY in env:
  python mcp-server/server.py
Or: cd mcp-server && python server.py

This server does not log HTTP requests or responses (to avoid accidental
logging of API keys or PII).
"""

from mcp.server.fastmcp import FastMCP

try:
    from .tools import tmdb_tools
except ImportError:
    from tools import tmdb_tools

mcp = FastMCP("TMDB", json_response=True)


@mcp.tool()
def get_configuration() -> str:
    """Get API configuration: image base URLs, languages, countries, timezones. Use when building image URLs or needing locale data."""
    return tmdb_tools.get_configuration()


@mcp.tool()
def search_movie(query: str, page: int = 1) -> str:
    """Search for movies by title. Use when the user asks about movies, film titles, or wants to find a specific movie."""
    return tmdb_tools.search_movie(query, page)


@mcp.tool()
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
    """Discover movies with filters and sort. Use when the user wants to browse movies by genre, year, rating, popularity, etc."""
    return tmdb_tools.discover_movie(
        sort_by=sort_by,
        page=page,
        language=language,
        primary_release_year=primary_release_year,
        vote_average_gte=vote_average_gte,
        vote_average_lte=vote_average_lte,
        with_genres=with_genres,
        year=year,
    )


@mcp.tool()
def search_tv(query: str, page: int = 1) -> str:
    """Search for TV shows by title. Use when the user asks about TV series, shows, or wants to find a specific program."""
    return tmdb_tools.search_tv(query, page)


@mcp.tool()
def get_movie_details(movie_id: int) -> str:
    """Get full details for a movie by its TMDB ID. Use after search_movie when more info (cast, overview, etc.) is needed."""
    return tmdb_tools.get_movie_details(movie_id)


@mcp.tool()
def get_tv_details(tv_id: int) -> str:
    """Get full details for a TV show by its TMDB ID. Use after search_tv when more info (cast, seasons, overview) is needed."""
    return tmdb_tools.get_tv_details(tv_id)


@mcp.tool()
def get_trending_movies(time_window: str = "day") -> str:
    """Get currently trending movies. time_window: 'day' or 'week'. Use when the user asks what's popular, trending, or hot now."""
    return tmdb_tools.get_trending_movies(time_window)


@mcp.tool()
def get_trending_tv(time_window: str = "day") -> str:
    """Get currently trending TV shows. time_window: 'day' or 'week'. Use when the user asks what's popular or trending on TV."""
    return tmdb_tools.get_trending_tv(time_window)


if __name__ == "__main__":
    mcp.run()
