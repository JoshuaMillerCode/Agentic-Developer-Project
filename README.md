# Agentic Developer Project

An agent-driven web app: **Reel Recs** frontend → LLM Agent backend (LangChain) → MCP Server wrapper → [TMDB API](https://developer.themoviedb.org/docs/getting-started).

**Full documentation for new developers:** [docs/](docs/) — start with [Getting started](docs/GETTING_STARTED.md).

---

## Quick start

**Run order:** Backend first (it spawns the MCP server), then frontend.

1. **Environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set:
   - **TMDB_API_KEY** — [TMDB API Settings](https://www.themoviedb.org/settings/api)
   - **ANTHROPIC_API_KEY** (or **OPENAI_API_KEY**) — for the LLM agent ([Anthropic](https://console.anthropic.com/) / [OpenAI](https://platform.openai.com/api-keys))

   Do not commit `.env`; it is in `.gitignore`.

2. **Backend** (from project root)
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r mcp-server/requirements.txt
   pip install -r backend/requirements.txt
   set -a && source .env 2>/dev/null || true; set +a
   python -m backend
   ```
   Backend: **http://localhost:8000**

3. **Frontend**
   ```bash
   cd frontend && npm install && npm run dev
   ```
   App: **http://localhost:3000**

Step-by-step setup, prerequisites, and verification: **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)**.

---

## Repo structure

| Folder | Purpose |
|--------|---------|
| **frontend/** | Reel Recs — Next.js web UI (chat, discovery rows, detail pages). All data via backend; no API keys on client. |
| **backend/** | LLM Agent — FastAPI + LangChain/LangGraph, MCP tools, `/chat`, discovery, configuration. Spawns MCP server. |
| **mcp-server/** | MCP wrapper around TMDB — exposes search, discover, details, trending as tools for the agent. |

**Component READMEs (setup, API, code layout):**

- [frontend/README.md](frontend/README.md) — Reel Recs overview, quick start, env, structure, features.
- [backend/README.md](backend/README.md) — API reference (chat, discovery, config), card shapes, errors, tests.
- [mcp-server/README.md](mcp-server/README.md) — Tools list, run instructions, env, production, tests.

**Docs:** [docs/README.md](docs/README.md) — index. [Architecture](docs/ARCHITECTURE.md), [Code structure](docs/CODE_STRUCTURE.md), [Dependencies](docs/DEPENDENCIES.md), [Documentation philosophy](docs/DOCUMENTATION_PHILOSOPHY.md).

---

## Dependencies

- **Python:** `mcp-server/requirements.txt` and `backend/requirements.txt` (use root `.venv`). See [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md).
- **Node:** `frontend/package.json` — run `npm install` in `frontend/`.

---

## Documentation

The [docs/](docs/) folder contains full project documentation for new and collaborating developers:

- **[Getting started](docs/GETTING_STARTED.md)** — Clone, venv, env vars, API keys, run order, verify.
- **[Architecture](docs/ARCHITECTURE.md)** — Diagram, data flow, security (keys in env only).
- **[Code structure](docs/CODE_STRUCTURE.md)** — Where to find and change code; links to component READMEs.
- **[Dependencies](docs/DEPENDENCIES.md)** — All dependency files and install commands.
- **[Documentation philosophy](docs/DOCUMENTATION_PHILOSOPHY.md)** — How docs are organized for onboarding.
