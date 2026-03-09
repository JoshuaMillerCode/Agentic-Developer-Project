# Architecture

High-level architecture of the Agentic Developer Project and how data and API keys flow through the system.

---

## Overview

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  Frontend Web   │────▶│  LLM Agent Backend   │────▶│  MCP Server     │
│  App (Reel Recs)│     │  (LangChain + tools)  │     │  (API Wrapper)   │
└─────────────────┘     └──────────────────────┘     └────────┬────────┘
         │                            │                        │
         │                            │                        ▼
         │                            │               ┌─────────────────┐
         │                            │               │  TMDB REST API  │
         │                            │               │  (3rd party)    │
         └────────────────────────────┘               └─────────────────┘
```

- **Frontend** — Next.js app (Reel Recs). Users type questions and see AI replies with inline movie/TV/person cards. All server calls go to the backend; no API keys on the client.
- **Backend** — FastAPI + LangChain/LangGraph. Runs a ReAct agent that can call MCP tools. Exposes `/chat`, `/configuration`, and discovery endpoints. Spawns the MCP server as a subprocess (stdio).
- **MCP Server** — Wraps the TMDB API and exposes tools (search, discover, details, trending, etc.). The agent calls these tools to answer user questions.
- **TMDB API** — The Movie Database public REST API. Used for movie/TV/person data.

---

## Separation of concerns

| Layer | Responsibility |
|-------|-----------------|
| **Frontend** | UI, user input, display of agent replies and cards, discovery rows, detail pages. No secrets. |
| **Backend** | Agent orchestration, tool calling (via MCP), LLM calls, card extraction, discovery/config HTTP client. Holds LLM and TMDB keys (via env). |
| **MCP Server** | TMDB API wrapper; exposes tools for the agent. Reads `TMDB_API_KEY` from env. |
| **TMDB** | Source of movie/TV/person data. |

---

## Key flows

**Chat (user question → answer with cards):**

1. User submits a message in the frontend.
2. Frontend sends `POST /chat` with `{ "message": "..." }` (and optional `region`) to the backend.
3. Backend runs the LangChain/LangGraph agent. The agent may call MCP tools (e.g. search_movie, discover_movie, get_movie_details).
4. MCP server (subprocess) receives tool calls, calls the TMDB API, returns results.
5. Backend aggregates tool results, gets the final text reply from the LLM, extracts **cards** (movie/TV/person) from tool output, filters to titles/names mentioned in the reply, and returns `{ response, reply_found, cards }`.
6. Frontend renders the reply (markdown) and displays cards below; cards link to detail pages.

**Discovery (rows on the home page):**

1. Frontend calls backend endpoints such as `/discovery/movies/popular`, `/discovery/movies/now-playing`, `/discovery/tv/popular`, `/discovery/people/trending` (with optional `region` and `page`).
2. Backend uses a minimal TMDb HTTP client (`tmdb_client.py`) for these routes — no agent, no MCP — and returns paginated results.
3. Frontend renders horizontal scroll rows with the same card components used in chat.

**Configuration (image URLs):**

1. Frontend calls `GET /configuration` once (e.g. on load).
2. Backend returns TMDB image base URLs and poster sizes from the same TMDb client.
3. Frontend builds poster/profile URLs as `{base_url}{size}{path}`.

---

## Security

- **API keys** — All keys (TMDB, Anthropic/OpenAI) are read from **environment variables** (e.g. `.env` at project root). Never committed; `.env` is in `.gitignore`.
- **Frontend** — No API keys. All external and LLM access goes through the backend.
- **CORS** — Backend allows configured origins (default: `http://localhost:3000`, `http://localhost:5173`). Set `CORS_ORIGINS` for production.

---

## Run order

1. **Backend** — Start first. It spawns the MCP server as a subprocess, so you do not start the MCP server separately for normal development.
2. **Frontend** — Start after the backend is up so the app can call `/configuration`, `/chat`, and discovery endpoints.

For full setup steps, see [Getting started](GETTING_STARTED.md). For component-level detail, see [Backend README](../backend/README.md), [MCP Server README](../mcp-server/README.md), and [Frontend README](../frontend/README.md).
