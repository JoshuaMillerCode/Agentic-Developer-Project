# Documentation philosophy

This document describes how documentation is organized so that a **new or collaborating developer** can onboard quickly and know where to look for setup, architecture, and code.

---

## Goals

- **Single entry point** — The project root [README.md](../README.md) and this [docs/](.) folder are the main entry. New developers start with the root README and [Getting started](GETTING_STARTED.md).
- **No secrets in repo** — API keys and env vars are documented in `.env.example` and in the docs; real values live only in `.env` (gitignored).
- **Clear run order** — Backend first (it spawns the MCP server), then frontend. Documented in README and [Getting started](GETTING_STARTED.md).
- **Component READMEs** — Each part of the stack (frontend, backend, MCP server) has its own README for setup, API reference, and code layout. The main docs link to them instead of duplicating detail.

---

## Where to look

| Need | Where to look |
|------|----------------|
| First-time setup (clone, env, keys, run) | [Getting started](GETTING_STARTED.md) |
| How the system fits together | [Architecture](ARCHITECTURE.md) |
| Where code lives (folders, files) | [Code structure](CODE_STRUCTURE.md) + [frontend/README.md](../frontend/README.md), [backend/README.md](../backend/README.md), [mcp-server/README.md](../mcp-server/README.md) |
| Dependency files and install | [Dependencies](DEPENDENCIES.md) |
| Backend API (chat, discovery, config, errors) | [backend/README.md](../backend/README.md) |
| MCP tools list and run instructions | [mcp-server/README.md](../mcp-server/README.md) |
| Frontend features and structure | [frontend/README.md](../frontend/README.md) |
| Env vars and keys | [.env.example](../.env.example), [Getting started](GETTING_STARTED.md) |

---

## Key flows (for onboarding)

1. **User question → answer:** Frontend sends message to backend `/chat` → backend runs agent → agent calls MCP tools → MCP calls TMDB → backend returns text + cards → frontend renders reply and cards.
2. **Discovery rows:** Frontend calls backend discovery endpoints → backend uses TMDb HTTP client (no agent) → frontend renders rows.
3. **API keys:** Only in env (`.env`). Frontend has none; backend has LLM + TMDB; MCP server has TMDB.

---

## For maintainers

- Keep the root README short: quick start, env pointer, run order, links to **docs/** and to **frontend/**, **backend/**, **mcp-server/** READMEs.
- Keep **docs/** as the place for project-wide topics: getting started, architecture, code structure, dependencies, this philosophy.
- Keep component READMEs as the single source for that component’s API, structure, and run instructions.
- When adding env vars or new services, update `.env.example` and the relevant README or [Getting started](GETTING_STARTED.md).

This structure supports the project brief’s requirement that documentation be clear for collaborators and new developers taking over the project.
