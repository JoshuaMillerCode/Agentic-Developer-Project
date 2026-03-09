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
frontend/          # Reel Recs — Web UI (Phase 4 complete). Next.js 14, Tailwind, dark theme.
  src/app/         # App Router: layout (title Reel Recs), page (config, ChatSection, DiscoverySection)
                   #   movie/[id], tv/[id], person/[id] — detail pages (poster, cast, overview, etc.)
  src/components/
    cards/         # MovieCard, TVCard, PersonCard + CardRenderer (shared by chat and discovery)
    chat/          # ChatSection (input, response, cards), MarkdownResponse (react-markdown), ChatLoading (film strip)
    discovery/     # DiscoverySection (four rows), CountryFilter (region dropdown)
  src/lib/         # api.ts (config, postChat, discovery with region, detail APIs, buildImageUrl), types.ts
  README.md        # Single entry point: overview, quick start, env, structure, features, backend relationship
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
- **Discovery region:** Optional `region` (ISO 3166-1, e.g. US) on `/discovery/movies/popular` and `/discovery/movies/now-playing`; passed to TMDb. **Chat region:** Optional `region` in POST /chat body; backend injects instruction so agent passes region to discover_movie, get_movie_popular, get_movie_now_playing.
- **Card filtering:** Only cards whose title/name appears in the AI reply in a **title-like context** (e.g. "Rocky (1976)", not "boxing" in "boxing movies") are returned; word-boundary and suffix checks avoid false matches. If none match, cards array is empty (no fallback to unrelated tool results).
- **Rate limits:** System prompt tells agent to minimize tool calls (one discover or one search for genre queries); `recursion_limit: 8` on agent invoke; 429 retries with exponential backoff (2.5s, 6s, 12s).

---

## Frontend (Phase 4 complete)

- **Name:** Reel Recs — AI-powered movie & TV picks.
- **Stack:** Next.js 14 (App Router), TypeScript, Tailwind CSS. All data from backend; no API keys on client. Env: `NEXT_PUBLIC_API_URL` (default http://localhost:8000).
- **Run:** Backend must be running first. Then: `cd frontend`, `npm install` (first time), `npm run dev` → http://localhost:3000.
- **Layout:** Hero chat at top (single input + "Ask" button); AI response and inline cards below; discovery section with four horizontal scroll rows; country filter in header.
- **Chat:** User types in hero input; POST /chat with message and optional region. Response is rendered as **markdown** (react-markdown + remark-gfm): headings, lists, bold, links, code blocks, blockquotes, tables, styled for dark theme (white headings, accent-red links, surface-700/800 code blocks). Cards from response (movie/TV/person) shown below the text; cards link to detail pages. **Loading:** Film-strip animation + "Searching the vault…" while waiting. Last response persisted in sessionStorage.
- **Discovery:** Four rows: Currently Popular Movies, Now Playing in Theaters, Popular TV Series, Trending Actors. Each row uses same card components (compact size); horizontal scroll, no visible scrollbar. Optional **region** (from CountryFilter) passed to popular/now-playing movie APIs so rows respect selected country.
- **Country filter:** Dropdown in header (All regions, US, GB, CA, AU, DE, FR, IN, JP, KR, ES, IT, BR, MX). Value stored in page state; passed to ChatSection (so POST /chat includes region) and DiscoverySection (so movie discovery rows use region).
- **Detail pages:** Clicking a movie/TV/person card goes to `/movie/[id]`, `/tv/[id]`, or `/person/[id]`. Detail pages show poster, title/name, year/dates, rating, overview, genres, cast (movie/TV), credits (person); "← Back to Reel Recs" link. Data from GET /movies/:id, /tv/:id, /people/:id.
- **Images:** Poster and profile URLs built in `buildImageUrl` from GET /configuration; profile images prefer larger TMDb sizes (h632, w300, w185) to avoid blur.
- **Docs:** `frontend/README.md` — overview, prerequisites, quick start, env, project structure, main features (chat, discovery, country filter, detail pages, loading), scripts, backend relationship.

---

## Decisions made

- Venv at project root (not inside mcp-server).
- TMDB auth via `api_key` query param (Bearer optional; not used in server).
- Production hardening applied: 429 → `rate_limit_exceeded`, query cap 500 chars, error-shape tests, README production section, no logging of requests/responses.
- Tests: pytest; python-dotenv in conftest; validation tests no key; integration tests skipped if no key.
- **Backend:** Chat returns structured `cards` (movie/TV/person) extracted from agent tool results; discovery and config use a separate TMDb HTTP client (`tmdb_client.py`) so the frontend can load discovery sections without invoking the agent. Validation (page 1–500, language ≤10 chars, time_window day|week) aligned with MCP; 400 for invalid params. No API keys in responses or logs. **Cards** come from search, details, credits, discovery, and trending tools; only items **mentioned in the AI reply** are returned (filter + cap 24), so broad prompts (e.g. “family movie night”) and specific prompts (e.g. “DiCaprio’s best movies”) both get relevant cards when the agent uses those tools.
- **Frontend:** Reel Recs branding; markdown-rendered AI response (react-markdown + remark-gfm); country filter (header) applied to discovery rows and chat; film-strip loading state; movie/TV/person detail pages; cards only for titles the backend returns (aligned with AI reply). Single frontend README as entry point.

---

## Key files to read in a new session

1. **EXECUTION_PLAN.md** — Full task list and phases.
2. **PROMPT_LOG.md** — Chronological prompts and outcomes (for demos/presentation).
3. **mcp-server/README.md** — Setup, run, tools, production, tests.
4. **.env.example** — Required env vars (TMDB_API_KEY, ANTHROPIC_API_KEY or OPENAI_API_KEY).
5. **backend/README.md** — Backend setup, run, full API reference (chat + cards, discovery, configuration), card shapes, errors, frontend integration.
6. **frontend/README.md** — Reel Recs overview, quick start, env, structure, features (chat, discovery, country filter, detail pages, markdown, loading), backend relationship.

- **Next session: start here**

- **Phase 5:** Update root README with run order (backend spawns MCP; backend then frontend), env setup, code structure. Phase 4 frontend is complete (Reel Recs: chat, discovery, country filter, detail pages, markdown response, loading animation).
