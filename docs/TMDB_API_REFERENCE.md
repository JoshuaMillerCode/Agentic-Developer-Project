# TMDB API v3 — Quick Reference

Documentation researched from [TMDB Developer Docs](https://developer.themoviedb.org/docs/getting-started). This page lists **every TMDB route wrapped by the MCP server** and the corresponding MCP tool name.

## Authentication

| Method | Usage |
|--------|-------|
| **API Key** | `?api_key=YOUR_KEY` on any request |
| **Bearer Token** | `Authorization: Bearer YOUR_ACCESS_TOKEN` (recommended for v3 + v4) |

Both are available in [TMDB API Settings](https://www.themoviedb.org/settings/api).

## Base URL

```
https://api.themoviedb.org/3
```

## Routes wrapped by the MCP server

All routes are **GET**. Query parameters (e.g. `page`, `language`, `region`) are passed by the MCP tools; see [mcp-server/README.md](../mcp-server/README.md) for tool parameters.

### Configuration

| TMDB path | MCP tool | Purpose |
|-----------|----------|---------|
| `GET /configuration` | `get_configuration` | Image base URLs, languages, countries, timezones |

### Search

| TMDB path | MCP tool | Purpose |
|-----------|----------|---------|
| `GET /search/movie` | `search_movie` | Search movies by title (`query`, `page`, `language`) |
| `GET /search/tv` | `search_tv` | Search TV shows by title (`query`, `page`, `language`) |
| `GET /search/person` | `search_person` | Search people by name (`query`, `page`, `language`) |
| `GET /search/multi` | `search_multi` | Search across movies, TV, and people (`query`, `page`, `language`) |

### Discover

| TMDB path | MCP tool | Purpose |
|-----------|----------|---------|
| `GET /discover/movie` | `discover_movie` | Discover movies with filters (`sort_by`, `page`, `language`, `primary_release_year`, `vote_average.gte`/`.lte`, `with_genres`, `year`, optional `region`) |

### Movie lists

| TMDB path | MCP tool | Purpose |
|-----------|----------|---------|
| `GET /movie/now_playing` | `get_movie_now_playing` | Movies currently in theatres (`page`, `language`, optional `region`) |
| `GET /movie/popular` | `get_movie_popular` | Popular movies (`page`, `language`, optional `region`) |
| `GET /movie/top_rated` | `get_movie_top_rated` | Top rated movies (`page`, `language`) |
| `GET /movie/upcoming` | `get_movie_upcoming` | Upcoming movie releases (`page`, `language`) |

### Movie details & credits

| TMDB path | MCP tool | Purpose |
|-----------|----------|---------|
| `GET /movie/{id}` | `get_movie_details` | Movie details by TMDB ID |
| `GET /movie/{id}/credits` | `get_movie_credits` | Cast and crew for a movie |

### TV lists

| TMDB path | MCP tool | Purpose |
|-----------|----------|---------|
| `GET /tv/airing_today` | `get_tv_airing_today` | TV shows airing today (`page`, `language`) |
| `GET /tv/on_the_air` | `get_tv_on_the_air` | TV shows currently on the air (`page`, `language`) |
| `GET /tv/popular` | `get_tv_popular` | Popular TV shows (`page`, `language`) |
| `GET /tv/top_rated` | `get_tv_top_rated` | Top rated TV shows (`page`, `language`) |

### TV details, seasons & episodes

| TMDB path | MCP tool | Purpose |
|-----------|----------|---------|
| `GET /tv/{id}` | `get_tv_details` | TV show details by TMDB ID |
| `GET /tv/{id}/credits` | `get_tv_credits` | Cast and crew for a TV show |
| `GET /tv/{id}/season/{season_number}` | `get_tv_season_details` | Season details (`language`; season_number 0 = specials) |
| `GET /tv/{id}/season/{season_number}/episode/{episode_number}` | `get_tv_episode_details` | Episode details (`language`) |

### Trending

| TMDB path | MCP tool | Purpose |
|-----------|----------|---------|
| `GET /trending/all/{day\|week}` | `get_trending_all` | All trending (movies, TV, people) |
| `GET /trending/movie/{day\|week}` | `get_trending_movies` | Trending movies |
| `GET /trending/tv/{day\|week}` | `get_trending_tv` | Trending TV shows |
| `GET /trending/person/{day\|week}` | `get_trending_people` | Trending people |

### People

| TMDB path | MCP tool | Purpose |
|-----------|----------|---------|
| `GET /person/{id}` | `get_person_details` | Person details by TMDB ID |
| `GET /person/{id}/movie_credits` | `get_person_movie_credits` | Movie credits for a person |
| `GET /person/{id}/tv_credits` | `get_person_tv_credits` | TV credits for a person |

---

## Rate limiting

Legacy limits (~40 req/10s) are disabled. Upper limits ~40 req/sec. Respect `429` responses. The MCP server returns a JSON error on 429 and does not throttle; callers should retry with backoff.

## Image URLs

Call `/3/configuration` first to get `images.base_url`. Example poster path:

```
{base_url}w500{poster_path}
```
