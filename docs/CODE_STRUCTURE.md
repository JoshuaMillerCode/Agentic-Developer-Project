# Code structure

Where to find and change code in the repo. Each component has its own README with detailed structure and API reference.

---

## Repo layout

```
agentic-developer-project/
├── frontend/           # Reel Recs — Web UI
├── backend/            # LLM Agent (LangChain + FastAPI)
├── mcp-server/         # MCP wrapper around TMDB API
├── docs/               # Project documentation (this folder)
├── .env.example        # Template for API keys (copy to .env)
├── .env                # Your keys (do not commit)
├── requirements.txt    # Root Python deps note (see backend + mcp-server)
└── EXECUTION_PLAN.md   # Phase-by-phase task list
```

---

## Frontend (`frontend/`)

**Purpose:** Next.js web app (**Reel Recs**) — hero chat, AI responses with inline movie/TV/person cards, discovery rows, country filter, and detail pages. All data comes from the backend; no API keys on the client.

**Full details:** [frontend/README.md](../frontend/README.md)

| Path | Purpose |
|------|---------|
| `src/app/` | App Router: layout, home page, detail routes (`movie/[id]`, `tv/[id]`, `person/[id]`) |
| `src/components/chat/` | Chat input, AI response area, inline cards, loading state |
| `src/components/discovery/` | Discovery rows and country/region filter |
| `src/components/cards/` | Movie, TV, Person cards and CardRenderer |
| `src/lib/api.ts` | API client (config, chat, discovery, detail, image URLs) |
| `src/lib/types.ts` | TypeScript types for API responses and cards |

---

## Backend (`backend/`)

**Purpose:** LLM Agent backend. Connects to the MCP server (spawns it as subprocess), loads MCP tools into LangChain, runs a ReAct agent to answer user questions. Exposes `/chat` (with structured cards), `/configuration`, and discovery endpoints for the frontend.

**Full details:** [backend/README.md](../backend/README.md)

| Path | Purpose |
|------|---------|
| `app.py` | FastAPI app, lifespan (MCP + agent), routes: `/health`, `/chat`, `/configuration`, `/discovery/*`; card extraction from tool results |
| `tmdb_client.py` | Minimal TMDb HTTP client for discovery and configuration (no MCP) |
| `requirements.txt` | Backend Python deps (LangChain, FastAPI, uvicorn, httpx, etc.) |
| `requirements-dev.txt` | Test deps (pytest) |
| `tests/` | Route tests (health, chat, configuration, discovery) |

---

## MCP Server (`mcp-server/`)

**Purpose:** MCP (Model Context Protocol) server that wraps the TMDB API. Exposes tools for search, discover, details, trending, and more so the LLM agent can query movie/TV/person data.

**Full details:** [mcp-server/README.md](../mcp-server/README.md)

| Path | Purpose |
|------|---------|
| `server.py` | Entry point; FastMCP app and tool registration |
| `tools/tmdb_tools.py` | TMDB API wrapper (HTTP calls, validation, error handling) |
| `requirements.txt` | MCP runtime deps (mcp, httpx) |
| `requirements-dev.txt` | Test deps (pytest) |
| `tests/` | Validation and integration tests |

---

## Where to look for common tasks

| Task | Where to look |
|------|----------------|
| Change chat UI or discovery layout | [frontend/README.md](../frontend/README.md) → `src/components/chat/`, `src/components/discovery/` |
| Change agent behavior or prompts | [backend/README.md](../backend/README.md) → `backend/app.py` |
| Add or change an MCP tool | [mcp-server/README.md](../mcp-server/README.md) → `server.py`, `tools/tmdb_tools.py` |
| Change API response shape (e.g. cards) | Backend `app.py` (card models and extraction); frontend `src/lib/types.ts`, `src/lib/api.ts` |
| Env vars and API keys | `.env.example` at project root; [Getting started](GETTING_STARTED.md) |

For dependency files and versions, see [Dependencies](DEPENDENCIES.md).
