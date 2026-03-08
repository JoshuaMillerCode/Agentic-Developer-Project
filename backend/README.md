# LLM Agent Backend (Phase 3)

Backend that connects to the **TMDB MCP Server**, loads its tools via LangChain MCP adapters, and runs a **ReAct agent** (LangGraph) to answer user questions. Exposes **`/chat`** for the frontend.

## Prerequisites

- **MCP Server** must be running **or** the backend will start it automatically over stdio (default). The backend spawns the MCP server as a subprocess, so you do **not** need to run `mcp-server/server.py` separately.
- **Python 3.11+** and project root venv (`.venv`).
- **Env:** Copy `.env.example` to `.env` and set:
  - `TMDB_API_KEY` — for the MCP server (passed through to the subprocess).
  - `OPENAI_API_KEY` — for the LLM (or `ANTHROPIC_API_KEY` if using Anthropic; see below).

## Quick start

From **project root** (with venv active and `.env` loaded):

```bash
source .venv/bin/activate
set -a && source .env 2>/dev/null || true; set +a
pip install -r backend/requirements.txt
python -m backend
```

Server runs at **http://localhost:8000**. Endpoints:

- **GET /health** — liveness.
- **POST /chat** — body `{"message": "your question"}` → `{"response": "..."}`.

## LLM provider

- **OpenAI (default):** Set `OPENAI_API_KEY` in `.env`. Optional: `OPENAI_MODEL` (default `gpt-4o-mini`).
- **Anthropic:** Set `ANTHROPIC_API_KEY` and install `langchain-anthropic`. Optional: `ANTHROPIC_MODEL`. If both keys are set, OpenAI is used.

## Run order (if running MCP server separately)

The backend can **spawn the MCP server itself** (stdio subprocess), so normally you do **not** start the MCP server by hand. If you prefer to run the MCP server in another terminal (e.g. for debugging), you would need to use **HTTP transport** and point the backend at that server (not implemented in this minimal setup; the backend uses stdio by default).

## Dependencies

See `backend/requirements.txt`: `langchain-mcp-adapters`, `langgraph`, `langchain-openai`, `fastapi`, `uvicorn`, `python-dotenv`, etc.

## Code layout

| Path           | Purpose |
|----------------|--------|
| `app.py`       | FastAPI app, lifespan (MCP session + agent), `/health`, `/chat`. |
| `requirements.txt` | Backend Python deps. |
