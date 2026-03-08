# Agent / Project Memory

Compact context for new sessions. Update this file when major decisions or phases change.

---

## Project

- **Name:** Agentic Developer Project (AI Builder Candidate Project).
- **Goal:** Agent-driven web app: Frontend → LLM Agent Backend → MCP Server → public REST API (TMDB).
- **Plan:** `EXECUTION_PLAN.md` (phase-by-phase); **prompt/response log:** `PROMPT_LOG.md`.

---

## Status (as of this session)

| Phase | Done | Next |
|-------|------|------|
| **1** Foundation & API | ✅ | — |
| **2** MCP Server | ✅ | — |
| **3** LLM Agent Backend | ✅ | — |
| **4** Frontend | ✅ | — |
| **5** Documentation | ☐ | Root README, structure, docs philosophy |
| **6** Video | ☐ | Screen recording, prompts, deployment narrative |

---

## API: TMDB

- **Base URL:** `https://api.themoviedb.org/3`
- **Auth:** `TMDB_API_KEY` in env (query param `api_key`); get key at [TMDB API Settings](https://www.themoviedb.org/settings/api).
- **Ref:** `docs/TMDB_API_REFERENCE.md` (endpoints, rate ~40 req/s, 429 possible).

---

## Repo layout

```
frontend/          # Web UI — COMPLETE (Phase 4). Next.js, Tailwind, chat + discovery.
  src/app/         # App Router: layout, page (config fetch, ChatSection, DiscoverySection)
  src/components/  # cards (Movie/TV/Person), chat (ChatSection), discovery (DiscoverySection)
  src/lib/         # api.ts (config, chat, discovery), types.ts (Card, TmdbConfig, etc.)
backend/           # LLM Agent / LangChain — COMPLETE (Phase 3)
  app.py           # FastAPI, MCP stdio session, ReAct agent, /chat (with cards), /configuration, /discovery/*
  tmdb_client.py   # Minimal TMDb HTTP client for discovery + config (httpx; no MCP)
  requirements.txt # includes httpx
  requirements-dev.txt
  tests/           # pytest (health, chat, configuration, discovery)
  README.md        # Full API reference, card shapes, errors, frontend integration
mcp-server/        # MCP wrapper around TMDB — COMPLETE
  server.py        # FastMCP entry, registers tools
  tools/tmdb_tools.py
  tests/
  requirements.txt
  requirements-dev.txt
  README.md
.env.example       # TMDB_API_KEY=, ANTHROPIC_API_KEY= or OPENAI_API_KEY=
.gitignore
```

- **Venv:** At **project root** (`.venv`); used by mcp-server and future backend.
- **Env:** Copy `.env.example` → `.env`, set `TMDB_API_KEY`, and `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`) for the backend. Never commit `.env`.

---

## MCP Server (Phase 2 complete)

- **Transport:** stdio (default); optional HTTP via `mcp.run(transport='streamable-http')`.
- **Tools (8):** `get_configuration`, `search_movie`, `search_tv`, `discover_movie`, `get_movie_details`, `get_tv_details`, `get_trending_movies`, `get_trending_tv`.
- **Security:** Key from env only; no request/response logging; errors return safe JSON (`api_error`, `request_failed`, `rate_limit_exceeded` for 429); validation (page, IDs, query length 500, sort_by, time_window, year/vote_average, with_genres as digits).
- **Run:** From root: `source .venv/bin/activate`, load `.env`, `cd mcp-server && python server.py`. Or run only the backend (it spawns MCP via stdio).
- **Tests:** `cd mcp-server && pip install -r requirements-dev.txt && pytest tests/ -v`. Integration tests need `TMDB_API_KEY`.

---

## Backend (Phase 3 complete)

- **Stack:** FastAPI, LangGraph `create_react_agent`, `langchain-mcp-adapters` (stdio), LangChain Anthropic (primary) or OpenAI. TMDb data for discovery/config via `backend/tmdb_client.py` (httpx, sync; raises `TmdbClientError` on HTTP/network errors).
- **MCP:** Backend spawns MCP server subprocess (cwd=project root, env passed); no need to run MCP server separately. Agent uses MCP tools for chat; discovery/config routes call `tmdb_client` directly (no agent).
- **Endpoints:**
  - **GET /health** — 200 when agent ready, 503 otherwise.
  - **GET /configuration** — TMDb config (image base URLs, poster sizes). 503 if TMDB_API_KEY not set; 502 on upstream failure.
  - **GET /discovery/movies/popular**, **/discovery/movies/now-playing**, **/discovery/tv/popular** — Query: `page` (1–500), `language` (max 10 chars). Response: `{ results, page, total_pages, total_results }` with movie or TV cards.
  - **GET /discovery/people/trending** — Query: `time_window` (day|week), `page`. No `language` param (TMDb API limitation). Same response shape with person cards.
  - **POST /chat** — Body `{"message": "..."}` (1–32000 chars). Response: `{"response": "...", "reply_found": true|false, "cards": [...]}`. `cards` = array of **MovieCard** / **TVCard** / **PersonCard** derived from agent tool results; **only titles/names the AI actually mentions** in the reply are returned (in mention order), capped at 24. May be empty if the agent didn’t use card-yielding tools or didn’t mention specific titles.
- **Card models (chat + discovery):** Each card has `type` ("movie" | "tv" | "person"), `id`, and type-specific fields: movie (`title`, `poster_path`, `release_date`, `vote_average`, `overview`), TV (`name`, `poster_path`, `first_air_date`, …), person (`name`, `profile_path`, `known_for_department`, `known_for`, `biography`). Frontend uses these for inline chat cards and discovery rows; image URLs built from GET /configuration + `poster_path`/`profile_path`.
- **Validation:** Discovery routes validate `page` (1–500), `language` length (≤10), `time_window` (day|week for people); 400 with clear message on invalid. Chat message length via Pydantic.
- **Errors:** 400 (validation), 401 (invalid LLM key), 502 (TMDb/LLM failure), 503 (agent not ready, TMDb not configured), 500 (other). No API keys or stack traces in responses.
- **Card extraction:** Collects cards from **all** tools that return movies/TV/people: search_*, get_*_details, get_*_credits, **and** discover_movie, get_movie_popular, get_movie_top_rated, get_trending_*, get_tv_popular, etc. (`TOOLS_FOR_CHAT_CARDS` in `app.py`). Parses ToolMessage content as JSON; handles `results` lists, single objects, and cast/crew arrays; type inference uses `media_type` or field heuristics (person before TV to avoid misclassifying people). Dedup by `(type, id)`. Up to 200 candidates then **filtered to titles/names mentioned in the AI reply** (`_filter_cards_mentioned_in_response`), then capped at 24. So: broad queries like “family movie night” get cards when the agent uses discover/get_movie_top_rated; specific queries like “DiCaprio’s best movies” still only show cards the AI actually mentioned.
- **Env:** `ANTHROPIC_API_KEY` (primary) or `OPENAI_API_KEY`; `TMDB_API_KEY` (for MCP and tmdb_client). Optional: `ANTHROPIC_MODEL`, `CORS_ORIGINS`, `HOST`, `PORT`, `RELOAD`, `CHAT_CARDS_MAX` (default 24), `CHAT_CARDS_CANDIDATE_MAX` (default 200).
- **Run:** From root: `pip install -r backend/requirements.txt`, `python -m backend` (http://localhost:8000). **Tests:** `pip install -r backend/requirements-dev.txt`, `python -m pytest backend/tests -v` (15 tests; no MCP/LLM keys needed, discovery/config mocked).
- **Docs:** `backend/README.md` — full API reference (request/response, card shapes, error table), frontend integration (image URLs, CORS, no keys on client), prerequisites, LLM provider, CORS, code layout, tests.

---

## Decisions made

- Venv at project root (not inside mcp-server).
- TMDB auth via `api_key` query param (Bearer optional; not used in server).
- Production hardening applied: 429 → `rate_limit_exceeded`, query cap 500 chars, error-shape tests, README production section, no logging of requests/responses.
- Tests: pytest; python-dotenv in conftest; validation tests no key; integration tests skipped if no key.
- **Backend:** Chat returns structured `cards` (movie/TV/person) extracted from agent tool results; discovery and config use a separate TMDb HTTP client (`tmdb_client.py`) so the frontend can load discovery sections without invoking the agent. Validation (page 1–500, language ≤10 chars, time_window day|week) aligned with MCP; 400 for invalid params. No API keys in responses or logs. **Cards** come from search, details, credits, discovery, and trending tools; only items **mentioned in the AI reply** are returned (filter + cap 24), so broad prompts (e.g. “family movie night”) and specific prompts (e.g. “DiCaprio’s best movies”) both get relevant cards when the agent uses those tools.

---

## Key files to read in a new session

1. **EXECUTION_PLAN.md** — Full task list and phases.
2. **PROMPT_LOG.md** — Chronological prompts and outcomes (for demos/presentation).
3. **mcp-server/README.md** — Setup, run, tools, production, tests.
4. **.env.example** — Required env vars (TMDB_API_KEY, ANTHROPIC_API_KEY or OPENAI_API_KEY).
5. **backend/README.md** — Backend setup, run, full API reference (chat + cards, discovery, configuration), card shapes, errors, frontend integration.

- **Next session: start here**

- **Phase 5:** Update root README with run order (MCP via backend, backend, frontend), env setup, code structure. Optional: frontend README in frontend/ with npm scripts and NEXT_PUBLIC_API_URL.
