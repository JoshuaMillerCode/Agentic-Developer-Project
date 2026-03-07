# TMDB MCP Server

MCP (Model Context Protocol) server for the **Agentic Developer Project**. It wraps [The Movie Database (TMDB) API](https://developer.themoviedb.org/docs/getting-started) and exposes movie/TV search, discovery, details, and trending as MCP tools for the LLM agent backend. This README is the single entry point for setup, run order, and code structure when integrating or taking over this server.

## Overview

- **Purpose:** Expose TMDB as MCP tools so an LLM agent can search movies/TV, get details, and discover or trend content.
- **Transport:** stdio by default (for LangChain/MCP client integration); optional HTTP for tools like MCP Inspector.
- **Tools:** 8 tools — configuration, search (movie/TV), discover movies, details (movie/TV), trending (movie/TV). See [Tools](#tools) below.

## Quick start

Assuming the project root already has a `.venv` and a `.env` with `TMDB_API_KEY`:

```bash
# From project root
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r mcp-server/requirements.txt
set -a && source .env 2>/dev/null || true; set +a
cd mcp-server && python server.py
```

The server runs over **stdio**; the agent backend connects to it via the MCP client. Start this server before starting the LLM backend.

## Setup & environment

### Python and dependencies

- Use the project root virtualenv (e.g. `.venv`). Create if needed: `python3 -m venv .venv`.
- Install this server’s dependencies from project root:  
  `pip install -r mcp-server/requirements.txt`  
  See [Dependencies](#dependencies) and `mcp-server/requirements.txt` for details.

### API key

The server requires a TMDB API key. Set it via environment only (no defaults; the server will not start without it).

- **Option A — project `.env` (recommended):**  
  Copy from project root: `cp .env.example .env`, then edit `.env` and set `TMDB_API_KEY=your_key`.  
  Load before running: `set -a && source .env 2>/dev/null || true; set +a`.
- **Option B — export:**  
  `export TMDB_API_KEY=your_key_here`

Get a key at [TMDB API Settings](https://www.themoviedb.org/settings/api). Do not commit real keys; `.env` should be in `.gitignore`.

## How to run

**Run order:** Start the MCP server first, then the LLM backend (and frontend as needed). The backend connects to this server via MCP.

### stdio (default)

From project root (with venv active and `TMDB_API_KEY` loaded):

```bash
cd mcp-server
python server.py
```

Or from project root without `cd`:  
`python mcp-server/server.py`

### HTTP transport (optional)

For HTTP (e.g. MCP Inspector):

```bash
cd mcp-server
python -c "
from server import mcp
mcp.run(transport='streamable-http')
"
```

Connect to `http://localhost:8000/mcp`.

## Code structure (project layout)

| Path | Purpose |
|------|--------|
| `server.py` | Entry point; defines the FastMCP app and registers all 8 tools. Run this to start the server. |
| `tools/` | TMDB API wrapper. `tmdb_tools.py` implements the logic for each tool (HTTP calls, validation, error handling). |
| `tests/` | Pytest suite: validation tests (no API key) and integration tests (real API, require `TMDB_API_KEY`). See [Tests](#tests). |

To add or change tool behavior: edit `tools/tmdb_tools.py` and the corresponding `@mcp.tool()` in `server.py`.

## Dependencies

- **Runtime:** Listed in `requirements.txt` (e.g. `mcp`, `httpx`). Install with `pip install -r mcp-server/requirements.txt` from project root.
- **Tests:** `requirements-dev.txt` adds pytest etc. Use for running the test suite (see [Tests](#tests)).

For production, pin exact versions (e.g. `pip freeze | grep -E '^mcp |^httpx '`) and document in `requirements.txt`; see [Production / deployment](#production--deployment).

## Rate limiting

TMDB allows roughly 40 requests per second. The server does **not** throttle. On **429 (Too Many Requests)** the server returns:

`{"error": "rate_limit_exceeded", "status_code": 429, "detail": "..."}`

Clients (or the agent) should retry with backoff. Other HTTP errors are returned as `api_error` with `status_code`.

Parameter notes: optional `discover_movie` parameters (e.g. `year`, `vote_average_gte`/`lte`, `primary_release_year`) are validated when provided (type and range); `with_genres` must be comma-separated genre IDs (digits). Search query length is capped at 500 characters.

## Production / deployment

- **API key:** Set only via environment (`TMDB_API_KEY`). No default; the server will not start without it.
- **Throttling:** The server does not throttle. TMDB allows ~40 req/s. On 429, the server returns `rate_limit_exceeded`; callers (or the agent) should retry with backoff.
- **Dependencies:** Pin exact versions for reproducible builds (e.g. `pip freeze | grep -E '^mcp |^httpx '` then set those in `requirements.txt`). See comments in `requirements.txt`.
- **Logging:** The server does not log HTTP requests or responses.
- **Timeout:** HTTP requests to TMDB use a 30-second timeout (configurable via `HTTP_TIMEOUT_SECONDS` in code).

## Tests

Tests cover all 8 tools: **validation** (no API key) and **integration** (requires `TMDB_API_KEY` in environment). Integration tests assume TMDB data for the used IDs (e.g. 603, 1396) remains available; they assert response structure and types, not exact titles.

From project root:

```bash
pip install -r mcp-server/requirements-dev.txt
python -m pytest mcp-server/tests/ -v
```

From `mcp-server`:

```bash
cd mcp-server
pip install -r requirements-dev.txt
pytest tests/ -v
```

- **Validation tests** run without an API key (empty query, invalid page/ID, invalid `sort_by`/`time_window`, etc.).
- **Integration tests** (marked `@pytest.mark.integration`) are skipped if `TMDB_API_KEY` is not set; with a valid key they call the real TMDB API and assert response structure.

Validation only:  
`pytest tests/ -v -m "not integration"`  
(or from root: `python -m pytest mcp-server/tests/ -v -m "not integration"`).

## Tools

| Tool | Description |
|------|-------------|
| `get_configuration` | API configuration (image URLs, languages, countries) |
| `search_movie` | Search movies by title |
| `search_tv` | Search TV shows by title |
| `discover_movie` | Discover movies with filters (genre, year, rating, sort) |
| `get_movie_details` | Movie details by TMDB ID |
| `get_tv_details` | TV show details by TMDB ID |
| `get_trending_movies` | Trending movies (day/week) |
| `get_trending_tv` | Trending TV (day/week) |
