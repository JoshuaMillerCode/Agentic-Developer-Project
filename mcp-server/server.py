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


# Configuration
@mcp.tool()
def get_configuration() -> str:
    """Get API configuration: image base URLs, languages, countries, timezones. Use when building image URLs or needing locale data."""
    return tmdb_tools.get_configuration()


# Search
@mcp.tool()
def search_movie(query: str, page: int = 1, language: str = "en-US") -> str:
    """Search for movies by title. Use when the user asks about movies, film titles, or wants to find a specific movie."""
    return tmdb_tools.search_movie(query, page, language)


# Discover
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
    region: str | None = None,
) -> str:
    """Discover movies with filters and sort. Use when the user wants to browse movies by genre, year, rating, popularity, or country. region: optional 2-letter ISO country code (e.g. US) to filter by country."""
    return tmdb_tools.discover_movie(
        sort_by=sort_by,
        page=page,
        language=language,
        primary_release_year=primary_release_year,
        vote_average_gte=vote_average_gte,
        vote_average_lte=vote_average_lte,
        with_genres=with_genres,
        year=year,
        region=region,
    )


# Search (continued)
@mcp.tool()
def search_tv(query: str, page: int = 1, language: str = "en-US") -> str:
    """Search for TV shows by title. Use when the user asks about TV series, shows, or wants to find a specific program."""
    return tmdb_tools.search_tv(query, page, language)


# Movies & TV (details)
@mcp.tool()
def get_movie_details(movie_id: int) -> str:
    """Get full details for a movie by its TMDB ID. Use after search_movie when more info (cast, overview, etc.) is needed."""
    return tmdb_tools.get_movie_details(movie_id)


@mcp.tool()
def get_tv_details(tv_id: int) -> str:
    """Get full details for a TV show by its TMDB ID. Use after search_tv when more info (cast, seasons, overview) is needed."""
    return tmdb_tools.get_tv_details(tv_id)


# Trending
@mcp.tool()
def get_trending_movies(time_window: str = "day") -> str:
    """Get currently trending movies. time_window: 'day' or 'week'. Use when the user asks what's popular, trending, or hot now."""
    return tmdb_tools.get_trending_movies(time_window)


@mcp.tool()
def get_trending_tv(time_window: str = "day") -> str:
    """Get currently trending TV shows. time_window: 'day' or 'week'. Use when the user asks what's popular or trending on TV."""
    return tmdb_tools.get_trending_tv(time_window)


# Movie Lists
@mcp.tool()
def get_movie_now_playing(page: int = 1, language: str = "en-US", region: str | None = None) -> str:
    """Get movies currently in theatres. region: optional 2-letter ISO country code (e.g. US) to filter by country. Use when the user asks what's in cinemas or now playing."""
    return tmdb_tools.get_movie_now_playing(page, language, region)


@mcp.tool()
def get_movie_popular(page: int = 1, language: str = "en-US", region: str | None = None) -> str:
    """Get popular movies. region: optional 2-letter ISO country code (e.g. US). Use when the user asks for popular or trending movies (list form)."""
    return tmdb_tools.get_movie_popular(page, language, region)


@mcp.tool()
def get_movie_top_rated(page: int = 1, language: str = "en-US") -> str:
    """Get top rated movies. Use when the user asks for best or highest-rated films."""
    return tmdb_tools.get_movie_top_rated(page, language)


@mcp.tool()
def get_movie_upcoming(page: int = 1, language: str = "en-US") -> str:
    """Get upcoming movie releases. Use when the user asks what's coming soon to theatres."""
    return tmdb_tools.get_movie_upcoming(page, language)


# Trending (additional)
@mcp.tool()
def get_trending_all(time_window: str = "day") -> str:
    """Get all trending content (movies, TV, people) in one list. time_window: 'day' or 'week'."""
    return tmdb_tools.get_trending_all(time_window)


@mcp.tool()
def get_trending_people(time_window: str = "day") -> str:
    """Get trending people (actors, etc.). time_window: 'day' or 'week'. Use when the user asks who's trending."""
    return tmdb_tools.get_trending_people(time_window)


# TV Series Lists
@mcp.tool()
def get_tv_airing_today(page: int = 1, language: str = "en-US") -> str:
    """Get TV shows airing today. Use when the user asks what's on TV today."""
    return tmdb_tools.get_tv_airing_today(page, language)


@mcp.tool()
def get_tv_on_the_air(page: int = 1, language: str = "en-US") -> str:
    """Get TV shows currently on the air (airing this season). Use for currently running series."""
    return tmdb_tools.get_tv_on_the_air(page, language)


@mcp.tool()
def get_tv_popular(page: int = 1, language: str = "en-US") -> str:
    """Get popular TV shows. Use when the user asks for popular series."""
    return tmdb_tools.get_tv_popular(page, language)


@mcp.tool()
def get_tv_top_rated(page: int = 1, language: str = "en-US") -> str:
    """Get top rated TV shows. Use when the user asks for best or highest-rated series."""
    return tmdb_tools.get_tv_top_rated(page, language)


# TV Seasons & Episodes
@mcp.tool()
def get_tv_season_details(tv_id: int, season_number: int, language: str = "en-US") -> str:
    """Get details for a specific TV season. tv_id: TMDB show ID; season_number: 1-based (0 for specials). Use after get_tv_details when user wants episode list or season info."""
    return tmdb_tools.get_tv_season_details(tv_id, season_number, language)


@mcp.tool()
def get_tv_episode_details(tv_id: int, season_number: int, episode_number: int, language: str = "en-US") -> str:
    """Get details for a specific TV episode. Use when the user asks about a particular episode (e.g. S01E05)."""
    return tmdb_tools.get_tv_episode_details(tv_id, season_number, episode_number, language)


@mcp.tool()
def get_tv_credits(tv_id: int) -> str:
    """Get cast and crew for a TV show. Use when the user asks who's in a series or for cast list."""
    return tmdb_tools.get_tv_credits(tv_id)


# Search (additional)
@mcp.tool()
def search_person(query: str, page: int = 1, language: str = "en-US") -> str:
    """Search for people (actors, directors, crew) by name. Use when the user asks about a person or wants to find someone's filmography."""
    return tmdb_tools.search_person(query, page, language)


@mcp.tool()
def search_multi(query: str, page: int = 1, language: str = "en-US") -> str:
    """Search across movies, TV shows, and people in one request. Use when the user's query could match any type (e.g. a title that is both a movie and a show)."""
    return tmdb_tools.search_multi(query, page, language)


# People
@mcp.tool()
def get_person_details(person_id: int) -> str:
    """Get full details for a person by TMDB ID. Use after search_person when more info (bio, birthday, etc.) is needed."""
    return tmdb_tools.get_person_details(person_id)


@mcp.tool()
def get_person_movie_credits(person_id: int) -> str:
    """Get movie credits (cast/crew) for a person. Use when the user asks what movies an actor or crew member has been in."""
    return tmdb_tools.get_person_movie_credits(person_id)


@mcp.tool()
def get_person_tv_credits(person_id: int) -> str:
    """Get TV credits (cast/crew) for a person. Use when the user asks what TV shows an actor or crew member has been in."""
    return tmdb_tools.get_person_tv_credits(person_id)


# Movies (additional)
@mcp.tool()
def get_movie_credits(movie_id: int) -> str:
    """Get cast and crew for a movie. Use when the user asks who's in a film or for the cast list."""
    return tmdb_tools.get_movie_credits(movie_id)


if __name__ == "__main__":
    mcp.run()
