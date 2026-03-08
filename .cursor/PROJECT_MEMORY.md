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
| **4** Frontend | ☐ | Simple UI, call backend |
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
frontend/          # Web UI (placeholder; Phase 4)
backend/           # LLM Agent / LangChain — COMPLETE (Phase 3)
  app.py           # FastAPI, MCP stdio session, ReAct agent, /chat
  requirements.txt
  README.md
mcp-server/        # MCP wrapper around TMDB — COMPLETE
  server.py        # FastMCP entry, registers 8 tools
  tools/tmdb_tools.py
  tests/           # pytest (validation + integration)
  requirements.txt
  requirements-dev.txt
  README.md        # Single entry point for MCP server
.env.example       # TMDB_API_KEY= (copy to .env)
.gitignore         # .env, venv, node_modules, etc.
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

- **Stack:** FastAPI, LangGraph `create_react_agent`, `langchain-mcp-adapters` (stdio), LangChain OpenAI (or Anthropic).
- **MCP:** Backend spawns MCP server subprocess (cwd=project root, env passed); no need to run MCP server separately.
- **Endpoints:** GET `/health`, POST `/chat` with body `{"message": "..."}` → `{"response": "..."}`.
- **Env:** `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`); `TMDB_API_KEY` passed to MCP subprocess.
- **Run:** From root: `pip install -r backend/requirements.txt`, `python -m backend` (port 8000).

---

## Decisions made

- Venv at project root (not inside mcp-server).
- TMDB auth via `api_key` query param (Bearer optional; not used in server).
- Production hardening applied: 429 → `rate_limit_exceeded`, query cap 500 chars, error-shape tests, README production section, no logging of requests/responses.
- Tests: pytest; python-dotenv in conftest; validation tests no key; integration tests skipped if no key.

---

## Key files to read in a new session

1. **EXECUTION_PLAN.md** — Full task list and phases.
2. **PROMPT_LOG.md** — Chronological prompts and outcomes (for demos/presentation).
3. **mcp-server/README.md** — Setup, run, tools, production, tests.
4. **.env.example** — Required env vars (TMDB_API_KEY, OPENAI_API_KEY or ANTHROPIC_API_KEY).
5. **backend/README.md** — Backend setup, run, /chat, LLM keys.

---

## Next session: start here

- **Phase 4:** Implement frontend (simple UI, call backend `/chat`, end-to-end flow).
- Backend is ready: `python -m backend` from project root with `.env` set.
