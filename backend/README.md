# LLM Agent Backend (Phase 3)

Backend that connects to the **TMDB MCP Server**, loads its tools via LangChain MCP adapters, and runs a **ReAct agent** (LangGraph) to answer user questions. Exposes **`/chat`** for the frontend.

## Prerequisites

- **MCP Server** must be running **or** the backend will start it automatically over stdio (default). The backend spawns the MCP server as a subprocess, so you do **not** need to run `mcp-server/server.py` separately.
- **Python 3.11+** and project root venv (`.venv`).
- **Env:** Copy `.env.example` to `.env` and set:
  - `TMDB_API_KEY` — for the MCP server (passed through to the subprocess).
  - `ANTHROPIC_API_KEY` — for the LLM (primary). Or `OPENAI_API_KEY` as alternative; see below.

## Quick start

From **project root** (with venv active and `.env` loaded):

```bash
source .venv/bin/activate
set -a && source .env 2>/dev/null || true; set +a
pip install -r backend/requirements.txt
python -m backend
```

Server runs at **http://localhost:8000**. This is suitable for **local development**. For production, set `RELOAD=false` and run behind a process manager (e.g. gunicorn with uvicorn workers); use env for `HOST`, `PORT`, and CORS (see below).

Endpoints:

- **GET /health** — Returns 200 only when the agent is ready (use for load balancers). Returns 503 before startup completes.
- **POST /chat** — Body `{"message": "your question"}` → `{"response": "...", "reply_found": true|false}`. `reply_found` is `false` when the agent could not produce a final text reply (e.g. only tool calls, no summary).

## LLM provider

- **Anthropic (primary):** Set `ANTHROPIC_API_KEY` in `.env`. Optional: `ANTHROPIC_MODEL` (default `claude-sonnet-4-6`). Valid IDs: `claude-sonnet-4-6`, `claude-sonnet-4-5`, `claude-opus-4-6`, `claude-haiku-4-5` (see [Anthropic models](https://docs.anthropic.com/en/docs/about-claude/models)). `LLM_TIMEOUT_SECONDS` (default 60).
- **OpenAI (alternative):** Set `OPENAI_API_KEY` to use OpenAI instead. Optional: `OPENAI_MODEL` (default `gpt-4o-mini`). If both keys are set, Anthropic is used.

## CORS and production config

- **CORS:** Set `CORS_ORIGINS` to a comma-separated list of allowed origins (e.g. `http://localhost:3000,http://localhost:5173`). If unset, defaults to `http://localhost:3000,http://localhost:5173` with `allow_credentials=true`. If `CORS_ORIGINS` is empty, the app allows any origin (`*`) with `allow_credentials=false` (valid for public APIs). Do not use `*` with credentials in production.
- **TMDB_API_KEY:** If not set at startup, the app logs a warning; the first MCP tool call that needs TMDB will fail with a clear error.
- **MCP_SERVER_SCRIPT:** Optional path to the MCP server script (absolute or relative to project root). Default: `mcp-server/server.py`.
- **Logging:** Non-sensitive request logging (method, path, status, duration) is emitted at INFO. Configure the `backend` logger or root logging for your environment; never log request bodies or headers that might contain keys.

## Run order (if running MCP server separately)

The backend can **spawn the MCP server itself** (stdio subprocess), so normally you do **not** start the MCP server by hand. If you prefer to run the MCP server in another terminal (e.g. for debugging), you would need to use **HTTP transport** and point the backend at that server (not implemented in this minimal setup; the backend uses stdio by default).

## Dependencies

See `backend/requirements.txt`: `langchain-mcp-adapters`, `langgraph`, `langchain-openai`, `fastapi`, `uvicorn`, `python-dotenv`, etc.

## Code layout

| Path           | Purpose |
|----------------|--------|
| `app.py`       | FastAPI app, lifespan (MCP session + agent), `/health`, `/chat`. System prompt in `app.py` maps all MCP tools so the LLM knows when to use each; tools are discovered at startup from the MCP server, so any new tools added to the MCP server are automatically available after restart. |
| `requirements.txt` | Backend Python deps. |
| `requirements-dev.txt` | Test deps (pytest). Install for running tests. |

## Tests

Route tests live in `backend/tests/` and use a test lifespan (no MCP or LLM keys required). From project root:

```bash
pip install -r backend/requirements-dev.txt
python -m pytest backend/tests -v
```
