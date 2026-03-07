# Agentic Developer Project

An agent-driven web app built with an MCP Server wrapper around a public REST API, an LLM Agent backend (LangChain), and a web frontend.

## API: The Movie Database (TMDB)

We use the [TMDB API v3](https://developer.themoviedb.org/docs/getting-started) for movie and TV data.

- **Register:** [TMDB Account → Settings → API](https://www.themoviedb.org/settings/api)
- **Auth:** API key as `api_key` query param, or Bearer token in `Authorization` header

## Environment Setup

1. Copy the example env file:
   ```bash
   cp .env.example .env
   ```
2. Add your TMDB API key in `.env`:
   ```
   TMDB_API_KEY=your_key_here
   ```
   Obtain your key at [TMDB API Settings](https://www.themoviedb.org/settings/api).

**Do not commit `.env`** — it is listed in `.gitignore`.

## MCP Server (Phase 2)

To run the TMDB MCP server:

```bash
source .venv/bin/activate
set -a && source .env 2>/dev/null || true; set +a
cd mcp-server && python server.py
```

See `mcp-server/README.md` for full instructions and tool list.

## Repo Structure

```
├── frontend/          # Web UI (to be added)
├── backend/           # LLM Agent (LangChain)
├── mcp-server/        # MCP wrapper around TMDB API (Phase 2 complete)
├── .env.example       # Template for API keys (copy to .env)
├── requirements.txt   # Python dependencies
└── EXECUTION_PLAN.md  # Phase-by-phase tasks
```
