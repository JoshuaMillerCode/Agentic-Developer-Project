---
name: documentation-readme
description: Keep README and project docs aligned with the Agentic Developer Project brief. Use when writing or updating README.md, onboarding docs, or documentation philosophy for collaborators or new developers taking over.
---

# Documentation & README (Project Brief Alignment)

## Purpose

The project brief requires: clear setup instructions, API key documentation, run order, code structure description, and a documentation philosophy for collaborators or new developers. This skill keeps README and docs consistent with those deliverables.

## README.md Must Include

1. **Setup & environment**
   - How to set up the environment (Python/Node versions, venv/npm install).
   - Where to obtain **third-party API key** and how to set it (e.g. `.env`, which variable).
   - Where to obtain **LLM API key** and how to set it.
   - `.env.example` or explicit list of required env vars (no real keys).

2. **How to run**
   - How to start the **MCP Server** (command, port, env vars).
   - How to start the **LLM backend/agent** (command, port, env vars).
   - How to start the **frontend** (command, port if relevant).
   - Order of startup (e.g. MCP first, then backend, then frontend).

3. **Code structure**
   - Brief description of folders: `frontend/`, backend or `agent/`, `mcp-server/`.
   - One-line purpose of each (e.g. "MCP Server: wraps the public REST API and exposes tools for the agent").

4. **Dependencies**
   - `requirements.txt` (Python) and/or `package.json` (Node) with versions.
   - No need to duplicate full lists in README if "see requirements.txt" is clear.

## Documentation Philosophy (for video / docs)

When describing docs for a new or collaborating developer:

- **README** is the single entry point: env setup, keys, run order, structure.
- **Architecture**: Frontend → Agent backend → MCP Server → external API; API keys only in env.
- **Key flows**: User question → backend → agent picks tools → MCP → external API → response to UI.
- **Where to look**: MCP tools in `mcp-server/`, agent and tool wiring in backend, UI in frontend.

## Checklist Before Submission

- [ ] README has third-party and LLM API key instructions (where to get, how to set).
- [ ] README has run instructions for MCP Server, backend, and frontend in order.
- [ ] README describes folder structure (frontend, backend/agent, mcp-server).
- [ ] Dependency files are present and referenced.
- [ ] No secrets in repo; `.env` (and equivalents) in `.gitignore`.
