# TMDB API v3 — Quick Reference

Documentation researched from [TMDB Developer Docs](https://developer.themoviedb.org/docs/getting-started).

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

## Key Endpoints (for MCP tools)

| Endpoint | Purpose |
|----------|---------|
| `GET /configuration` | Image base URLs, languages, countries |
| `GET /search/movie?query=...` | Search movies by title |
| `GET /search/tv?query=...` | Search TV shows |
| `GET /discover/movie` | Discover movies (filters, sort) |
| `GET /movie/{id}` | Movie details |
| `GET /tv/{id}` | TV show details |
| `GET /trending/movie/day` | Trending movies |
| `GET /trending/tv/day` | Trending TV |

## Rate Limiting

Legacy limits (~40 req/10s) are disabled. Upper limits ~40 req/sec. Respect `429` responses.

## Image URLs

Call `/3/configuration` first to get `images.base_url`. Example poster path:

```
{base_url}w500{poster_path}
```
