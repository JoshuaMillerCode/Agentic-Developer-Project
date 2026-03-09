# Dependencies

All dependency files and how to install them. Versions are pinned or ranged per component; for production, pin exact versions where appropriate.

---

## Python (backend + MCP server)

The project uses a **single virtualenv at the project root** for both the backend and the MCP server.

### Root

- **`requirements.txt`** (project root) — Short note only; actual deps live in `backend/` and `mcp-server/`.
- Install both:
  ```bash
  pip install -r mcp-server/requirements.txt
  pip install -r backend/requirements.txt
  ```

### MCP Server (`mcp-server/requirements.txt`)

- **mcp** — MCP server framework.
- **httpx** — HTTP client for TMDB API.

See [mcp-server/README.md](../mcp-server/README.md) for run instructions and production pinning.

### Backend (`backend/requirements.txt`)

- **langchain-mcp-adapters** — Connect LangChain to MCP tools (stdio).
- **langgraph** — ReAct agent.
- **langchain-anthropic**, **langchain-openai** — LLM providers.
- **fastapi**, **uvicorn** — HTTP API.
- **python-dotenv**, **httpx** — Env and HTTP.

See [backend/README.md](../backend/README.md) for API reference and tests.

### Optional: dev/test

- **MCP server tests:** `pip install -r mcp-server/requirements-dev.txt` then `pytest mcp-server/tests/ -v`.
- **Backend tests:** `pip install -r backend/requirements-dev.txt` then `pytest backend/tests/ -v`.

---

## Frontend (Node.js)

- **Location:** `frontend/package.json`
- **Install:** From project root, `cd frontend && npm install`.

### Main dependencies

- **next** — Next.js 14 (App Router).
- **react**, **react-dom** — UI.
- **react-markdown**, **remark-gfm** — Markdown rendering of AI replies.
- **tailwindcss** — Styling.

### Dev dependencies

- TypeScript, ESLint, PostCSS, Autoprefixer, Next.js config.

See [frontend/README.md](../frontend/README.md) for scripts (`npm run dev`, `build`, `start`, `lint`).

---

## Summary

| Component | Dependency file | Install command |
|-----------|-----------------|-----------------|
| MCP server | `mcp-server/requirements.txt` | `pip install -r mcp-server/requirements.txt` |
| Backend | `backend/requirements.txt` | `pip install -r backend/requirements.txt` |
| Frontend | `frontend/package.json` | `cd frontend && npm install` |

All from **project root** with the root `.venv` activated for Python. Full setup is in [Getting started](GETTING_STARTED.md).
