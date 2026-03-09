# LLM Agent Backend (Phase 3)

Backend that connects to the **TMDB MCP Server**, loads its tools via LangChain MCP adapters, and runs a **ReAct agent** (LangGraph) to answer user questions. Exposes **`/chat`** (with structured cards), **discovery**, and **configuration** endpoints for the AI Movie Assistant frontend.

## Prerequisites

- **MCP Server** — The backend spawns it as a subprocess (stdio); you do **not** need to run `mcp-server/server.py` separately. See [Run order](#run-order-if-running-mcp-server-separately) if you prefer to run it yourself.
- **Python 3.11+** and project root venv (`.venv`).
- **Env:** Copy `.env.example` to `.env` and set:
  - `TMDB_API_KEY` — for the MCP server (passed through to the subprocess).
  - `ANTHROPIC_API_KEY` — for the LLM (primary). Or `OPENAI_API_KEY` as alternative; see [LLM provider](#llm-provider).

## Quick start

From **project root** (with venv active and `.env` loaded):

```bash
source .venv/bin/activate
set -a && source .env 2>/dev/null || true; set +a
pip install -r backend/requirements.txt
python -m backend
```

Server runs at **http://localhost:8000** (suitable for local development). For production, set `RELOAD=false` and run behind a process manager; see [CORS and production config](#cors-and-production-config).

- **GET /health** — Returns 200 when the agent is ready (use for load balancers). Returns 503 before startup completes.
- Other endpoints: see [API reference](#api-reference) below.

---

## API reference

### Routes overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check; 200 when agent is ready, 503 before startup. |
| GET | `/configuration` | TMDb API configuration (image base URLs) for building poster/profile URLs. |
| GET | `/discovery/movies/popular` | Paginated list of currently popular movies. |
| GET | `/discovery/movies/now-playing` | Paginated list of movies now playing in theatres. |
| GET | `/discovery/tv/popular` | Paginated list of popular TV series. |
| GET | `/discovery/people/trending` | Paginated list of trending people (actors, etc.). |
| GET | `/movies/{movie_id}` | Movie detail: full info and cast. |
| GET | `/people/{person_id}` | Person detail: full info, biography, movie/TV credits. |
| GET | `/tv/{tv_id}` | TV show detail: full info and cast. |
| POST | `/chat` | Send a message; returns agent reply and optional cards (movie/TV/person). |

---

### POST /chat

Accepts a single user message and returns the agent’s text reply plus optional **cards** (movie, TV, or person) derived from agent tool results. Cards can be empty if the agent did not return structured data.

**Request body**

| Field     | Type   | Required | Constraints |
|----------|--------|----------|-------------|
| `message` | string | yes      | 1–32000 characters |
| `region`  | string | no       | Optional 2-letter ISO 3166-1 country code (e.g. `US`) to filter discovery content in the agent’s context. |

Example:

```json
{ "message": "What are some popular sci-fi movies from 2020?" }
```

**Response**

| Field          | Type    | Description |
|----------------|---------|-------------|
| `response`     | string  | The agent’s text reply. |
| `reply_found`  | boolean | `false` when the agent could not produce a final text reply. |
| `cards`        | array   | Zero or more card objects for inline rendering (see [Card shapes](#card-shapes)). Capped at `CHAT_CARDS_MAX` (default 24). |

Example:

```json
{
  "response": "Here are some popular sci-fi movies from 2020...",
  "reply_found": true,
  "cards": [
    {
      "type": "movie",
      "id": 12345,
      "title": "Example Movie",
      "poster_path": "/path.jpg",
      "release_date": "2020-01-15",
      "vote_average": 7.5,
      "overview": "Short description..."
    }
  ]
}
```

**Card shapes** — Each card has `type` and an `id`. Other fields depend on `type`; all non-id fields may be `null` or omitted.

- **Movie** (`type: "movie"`): `id`, `title`, `poster_path`, `release_date`, `vote_average`, `overview`.
- **TV** (`type: "tv"`): `id`, `name`, `poster_path`, `first_air_date`, `vote_average`, `overview`.
- **Person** (`type: "person"`): `id`, `name`, `profile_path`, `known_for_department`, `known_for` (array of strings, e.g. titles), `biography`.

Cards are parsed from MCP tool JSON output; invalid or non-list tool results yield an empty `cards` array. The number of cards returned is limited to `CHAT_CARDS_MAX` (env, default 24) so responses stay manageable (e.g. for “actor X’s movies” we return the first 24 cards from search/details/credits tools, not the full filmography).

---

### GET /configuration

Returns TMDb API configuration for building image URLs (e.g. poster and profile photos). No query parameters.

**Response** — TMDb config object. Relevant keys for the frontend:

- `images.base_url` — HTTP base URL for images.
- `images.secure_base_url` — HTTPS base URL for images.
- `images.poster_sizes` — Array of size suffixes (e.g. `"w342"`, `"w500"`).

Example (abbreviated):

```json
{
  "images": {
    "base_url": "http://image.tmdb.org/t/p/",
    "secure_base_url": "https://image.tmdb.org/t/p/",
    "poster_sizes": ["w92", "w154", "w185", "w342", "w500", "w780", "original"]
  }
}
```

**Errors**

- **503** — `TMDB_API_KEY` is not set (TMDb not configured).
- **502** — Upstream TMDb request failed (network or API error).

---

### GET /discovery/movies/popular  
### GET /discovery/movies/now-playing  
### GET /discovery/tv/popular

Paginated discovery lists: popular movies, now-playing movies, or popular TV series. Response shape is the same for all three.

**Query parameters**

| Parameter  | Type   | Default  | Description |
|------------|--------|----------|-------------|
| `page`     | int    | 1        | Page number, 1–500. |
| `language` | string | `en-US`  | Language code, max 10 characters. |
| `region`   | string | —        | Optional. 2-letter ISO 3166-1 country code (e.g. `US`, `GB`) to regionalize results. Applies only to the two movie endpoints (`/discovery/movies/popular`, `/discovery/movies/now-playing`). |

**Response**

| Field          | Type   | Description |
|----------------|--------|-------------|
| `results`      | array  | Movie cards (movies) or TV cards (TV). Same [card shapes](#card-shapes) as in `/chat` (movie vs tv). |
| `page`         | int    | Current page. |
| `total_pages`  | int    | Total pages. |
| `total_results`| int    | Total items. |

**Errors**

- **400** — Validation (e.g. `page` not in 1–500, `language` longer than 10 characters).
- **502** — TMDb/upstream failure.
- **503** — TMDb not configured (`TMDB_API_KEY` not set).

---

### GET /discovery/people/trending

Trending people (actors, etc.). This endpoint does **not** support a `language` query parameter (TMDb API limitation).

**Query parameters**

| Parameter     | Type   | Default | Description |
|---------------|--------|---------|-------------|
| `time_window` | string | `day`   | `"day"` or `"week"`. |
| `page`        | int    | 1       | Page number, 1–500. |

**Response** — Same structure as the other discovery endpoints: `results` (array of person cards), `page`, `total_pages`, `total_results`. Person cards use the same [card shapes](#card-shapes) as in `/chat`.

**Errors**

- **400** — Validation (e.g. `time_window` not `day` or `week`, `page` out of range).
- **502** — TMDb/upstream failure.
- **503** — TMDb not configured.

---

### GET /movies/{movie_id}

Movie detail (show) page: full movie info plus cast. Used when the user clicks a movie card.

**Path parameters**

| Parameter   | Type | Description |
|-------------|------|-------------|
| `movie_id`  | int  | TMDb movie ID (positive integer). |

**Query parameters**

| Parameter  | Type   | Default  | Description |
|------------|--------|----------|-------------|
| `language` | string | `en-US`  | Language code, max 10 characters. |

**Response** — `MovieDetailResponse`: card fields plus tagline, genres, runtime, and cast.

| Field          | Type    | Description |
|----------------|---------|-------------|
| `type`         | string  | `"movie"`. |
| `id`           | int     | TMDb movie ID. |
| `title`        | string  | Movie title (may be null). |
| `poster_path`  | string  | Poster path for image URL (may be null). |
| `release_date` | string  | Release date (may be null). |
| `vote_average` | float   | Average rating (may be null). |
| `overview`     | string  | Synopsis (may be null). |
| `tagline`      | string  | Tagline (may be null). |
| `genres`       | array   | List of genre objects. |
| `runtime`      | int     | Runtime in minutes (may be null). |
| `cast`         | array   | Cast members (see below). |

Each **cast** item: `id` (int), `name` (string), `character` (string), `profile_path` (string). All cast fields may be null except `id`.

**Errors**

- **400** — `movie_id` not a positive integer, or `language` longer than 10 characters.
- **502** — TMDb/upstream failure (e.g. movie not found or network error).
- **503** — TMDb not configured (`TMDB_API_KEY` not set).

---

### GET /people/{person_id}

Person detail page: full person info, biography, and movie/TV credits.

**Path parameters**

| Parameter   | Type | Description |
|-------------|------|-------------|
| `person_id` | int  | TMDb person ID (positive integer). |

**Query parameters**

| Parameter  | Type   | Default  | Description |
|------------|--------|----------|-------------|
| `language` | string | `en-US`  | Language code, max 10 characters. |

**Response** — `PersonDetailResponse`.

| Field                   | Type   | Description |
|-------------------------|--------|-------------|
| `type`                  | string | `"person"`. |
| `id`                    | int    | TMDb person ID. |
| `name`                  | string | Person name (may be null). |
| `profile_path`          | string | Profile photo path (may be null). |
| `known_for_department`  | string | e.g. Acting (may be null). |
| `known_for`             | array  | List of strings (titles). |
| `biography`             | string | Biography text (may be null). |
| `birthday`              | string | Birth date (may be null). |
| `place_of_birth`        | string | Place of birth (may be null). |
| `movie_credits`         | array  | List of movie credit objects (id, title, release_date, character). |
| `tv_credits`            | array  | List of TV credit objects (id, name, first_air_date, character). |

**Errors**

- **400** — `person_id` not a positive integer, or `language` longer than 10 characters.
- **502** — TMDb/upstream failure.
- **503** — TMDb not configured.

---

### GET /tv/{tv_id}

TV show detail page: full show info plus cast.

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tv_id`   | int  | TMDb TV show ID (positive integer). |

**Query parameters**

| Parameter  | Type   | Default  | Description |
|------------|--------|----------|-------------|
| `language` | string | `en-US`  | Language code, max 10 characters. |

**Response** — `TvDetailResponse`: card fields plus tagline, genres, number of seasons, and cast.

| Field              | Type   | Description |
|--------------------|--------|-------------|
| `type`             | string | `"tv"`. |
| `id`               | int    | TMDb TV show ID. |
| `name`             | string | Show name (may be null). |
| `poster_path`      | string | Poster path (may be null). |
| `first_air_date`   | string | First air date (may be null). |
| `vote_average`     | float  | Average rating (may be null). |
| `overview`         | string | Synopsis (may be null). |
| `tagline`          | string | Tagline (may be null). |
| `genres`           | array  | List of genre objects. |
| `number_of_seasons`| int    | Number of seasons (may be null). |
| `cast`             | array  | Cast members: `id`, `name`, `character`, `profile_path` (same shape as movie cast). |

**Errors**

- **400** — `tv_id` not a positive integer, or `language` longer than 10 characters.
- **502** — TMDb/upstream failure.
- **503** — TMDb not configured.

---

### Error responses (all endpoints)

| Code | Meaning |
|------|--------|
| **400** | Validation: invalid `page`, `language`, `time_window`, `region` (e.g. not a 2-letter code), or `message` (e.g. empty or over length). |
| **401** | Invalid LLM API key (e.g. `ANTHROPIC_API_KEY`). Returned only by `/chat`. |
| **502** | Upstream failure: TMDb API/network error or LLM service error (e.g. billing). |
| **503** | Service not ready: agent not initialized, or TMDb not configured (`TMDB_API_KEY` not set). |

Other server errors may return **500** with a generic message.

---

### Frontend integration

- **Image URLs** — Call **GET /configuration** once (e.g. at app load). Build poster/profile URLs as:  
  `{images.secure_base_url}{size}{poster_path|profile_path}`  
  e.g. `https://image.tmdb.org/t/p/w342/abc123.jpg`. Use a size from `poster_sizes` (e.g. `w342`, `w500`). Omit or use a placeholder when `poster_path` or `profile_path` is null.
- **CORS** — Configure `CORS_ORIGINS` for your frontend origin(s). Defaults allow `http://localhost:3000` and `http://localhost:5173`. See [CORS and production config](#cors-and-production-config).
- **Base URL** — Point the frontend at the backend base URL (e.g. `http://localhost:8000`). All TMDb and LLM access goes through the backend; no API keys are required on the client.

---

## LLM provider

- **Anthropic (primary):** Set `ANTHROPIC_API_KEY` in `.env`. Optional: `ANTHROPIC_MODEL` (default `claude-sonnet-4-6`). Valid IDs: `claude-sonnet-4-6`, `claude-sonnet-4-5`, `claude-opus-4-6`, `claude-haiku-4-5` (see [Anthropic models](https://docs.anthropic.com/en/docs/about-claude/models)). `LLM_TIMEOUT_SECONDS` (default 60).
- **OpenAI (alternative):** Set `OPENAI_API_KEY` to use OpenAI instead. Optional: `OPENAI_MODEL` (default `gpt-4o-mini`). If both keys are set, Anthropic is used.

## CORS and production config

- **CORS:** Set `CORS_ORIGINS` to a comma-separated list of allowed origins (e.g. `http://localhost:3000,http://localhost:5173`). If unset, defaults to `http://localhost:3000,http://localhost:5173` with `allow_credentials=true`. If `CORS_ORIGINS` is empty, the app allows any origin (`*`) with `allow_credentials=false`. Do not use `*` with credentials in production.
- **Server:** Set `HOST`, `PORT`, and `RELOAD=false` for production; run behind a process manager (e.g. gunicorn with uvicorn workers). See [Quick start](#quick-start).
- **TMDB_API_KEY:** If not set at startup, the app logs a warning; the first MCP tool call that needs TMDb will fail with a clear error.
- **MCP_SERVER_SCRIPT:** Optional path to the MCP server script (absolute or relative to project root). Default: `mcp-server/server.py`.
- **Logging:** Non-sensitive request logging (method, path, status, duration) is emitted at INFO. Configure the `backend` logger or root logging for your environment; never log request bodies or headers that might contain keys.

## Run order (if running MCP server separately)

The backend **spawns the MCP server itself** (stdio subprocess), so you normally do not start the MCP server by hand. To run it in another terminal (e.g. for debugging), you would need HTTP transport (not implemented in this setup).

## Dependencies

See `backend/requirements.txt`: `langchain-mcp-adapters`, `langgraph`, `langchain-openai`, `fastapi`, `uvicorn`, `python-dotenv`, `httpx`, etc. Install test deps from `backend/requirements-dev.txt` for [Tests](#tests).

## Code layout

| Path             | Purpose |
|------------------|--------|
| `app.py`         | FastAPI app, lifespan (MCP session + agent), routes: `/health`, `/chat` (with card extraction), `/configuration`, `/discovery/*` (movies/popular, movies/now-playing, tv/popular, people/trending), and detail routes `GET /movies/{movie_id}`, `GET /people/{person_id}`, `GET /tv/{tv_id}`. Card and detail response models; card extraction from agent tool results. |
| `tmdb_client.py` | Minimal TMDb HTTP client for discovery lists, configuration, and detail/credits (no MCP). |
| `requirements.txt`   | Backend Python deps (includes `httpx`). |
| `requirements-dev.txt` | Test deps (pytest). Install for running tests. |

## Tests

Route tests live in `backend/tests/` and use a test lifespan (no MCP or LLM keys required). From project root:

```bash
pip install -r backend/requirements-dev.txt
python -m pytest backend/tests -v
```
