# Agentic Developer Project — Documentation

This folder contains the full documentation for the **Agentic Developer Project**: an agent-driven web app with an MCP Server wrapper around the TMDB API, an LLM Agent backend (LangChain), and the **Reel Recs** frontend.

---

## Documentation index

| Document | Purpose |
|----------|---------|
| **[Getting started](GETTING_STARTED.md)** | Environment setup, API keys, run order, and first-time run. Start here if you're new to the project. |
| **[Architecture](ARCHITECTURE.md)** | High-level architecture, data flow, and security (API keys, CORS). |
| **[Code structure](CODE_STRUCTURE.md)** | Repo layout and links to component-specific READMEs (frontend, backend, MCP server). |
| **[Dependencies](DEPENDENCIES.md)** | Python and Node dependency files and how to install them. |
| **[Documentation philosophy](DOCUMENTATION_PHILOSOPHY.md)** | How docs are organized for new or collaborating developers. |

---

## Component READMEs (specifics)

For detailed setup, API reference, and code layout of each part of the stack:

- **[Frontend](../frontend/README.md)** — Reel Recs: Next.js UI, quick start, env, project structure, features, backend integration.
- **[Backend](../backend/README.md)** — LLM Agent: FastAPI, LangChain, MCP tools, full API reference (chat, discovery, configuration), card shapes, errors, tests.
- **[MCP Server](../mcp-server/README.md)** — TMDB MCP wrapper: tools list, run instructions, env, production notes, tests.

---

## Quick reference

- **Run order:** Backend first (it spawns the MCP server), then frontend.
- **Env:** Copy `.env.example` to `.env`; set `TMDB_API_KEY` and `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`).
- **Backend:** `http://localhost:8000` — [backend/README.md](../backend/README.md)
- **Frontend:** `http://localhost:3000` — [frontend/README.md](../frontend/README.md)

For step-by-step setup, see [Getting started](GETTING_STARTED.md).
