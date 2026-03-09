# Getting started

This guide gets a new developer from a fresh clone to a running **Reel Recs** app (frontend + backend + MCP server) in their own environment.

---

## Prerequisites

- **Git** — to clone the repo.
- **Python 3.11+** — for the backend and MCP server (shared virtualenv at project root).
- **Node.js** (LTS) — for the frontend (see [frontend/README.md](../frontend/README.md)).

---

## 1. Clone and enter the project

```bash
git clone <repo-url>
cd agentic-developer-project
```

---

## 2. Python environment

Create and activate a virtualenv at the **project root** (used by both the MCP server and the backend):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

---

## 3. Environment variables (API keys)

All secrets live in a `.env` file at the project root. Never commit `.env` (it is in `.gitignore`).

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Add your keys in `.env`:**

   | Variable | Required | Where to get it |
   |----------|----------|------------------|
   | `TMDB_API_KEY` | Yes | [TMDB API Settings](https://www.themoviedb.org/settings/api) — register and create an API key. |
   | `ANTHROPIC_API_KEY` | Yes (or OpenAI) | [Anthropic Console](https://console.anthropic.com/) — for the LLM agent. |
   | `OPENAI_API_KEY` | Alternative to Anthropic | [OpenAI API Keys](https://platform.openai.com/api-keys) — use if you prefer OpenAI instead of Anthropic. |

   The backend uses **Anthropic** if `ANTHROPIC_API_KEY` is set; otherwise it uses **OpenAI** when `OPENAI_API_KEY` is set. At least one LLM key is required for chat.

   See [.env.example](../.env.example) for optional overrides (CORS, model, timeouts, etc.).

---

## 4. Install dependencies

**Python (backend + MCP server):**

From project root with venv active:

```bash
pip install -r mcp-server/requirements.txt
pip install -r backend/requirements.txt
```

**Frontend:**

```bash
cd frontend
npm install
cd ..
```

See [Dependencies](DEPENDENCIES.md) for details and optional dev/test dependencies.

---

## 5. Run the application

**Run order:** Start the **backend** first (it spawns the MCP server automatically). Then start the **frontend**.

**Terminal 1 — Backend (and MCP server):**

```bash
source .venv/bin/activate
set -a && source .env 2>/dev/null || true; set +a
python -m backend
```

You should see the server listening at **http://localhost:8000**. The backend starts the MCP server as a subprocess; you do **not** need to run `mcp-server/server.py` separately.

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

Open **http://localhost:3000** in your browser. You should see **Reel Recs** with the hero chat and discovery rows.

---

## 6. Verify end-to-end

1. **Health:** Open http://localhost:8000/health — should return 200 when the agent is ready.
2. **Configuration:** Open http://localhost:8000/configuration — should return TMDB image config (requires `TMDB_API_KEY`).
3. **Chat:** In the Reel Recs UI, type e.g. “What are some popular sci-fi movies?” and click **Ask**. You should get an AI reply and optionally inline movie/TV/person cards.

If anything fails, check [Architecture](ARCHITECTURE.md) and the component READMEs: [backend/README.md](../backend/README.md), [frontend/README.md](../frontend/README.md), [mcp-server/README.md](../mcp-server/README.md).

---

## Optional: frontend environment

The frontend talks to the backend at `http://localhost:8000` by default. To override (e.g. different host/port), create `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

See [frontend/README.md](../frontend/README.md) for details.

---

## Next steps

- **[Architecture](ARCHITECTURE.md)** — How frontend, backend, MCP server, and TMDB fit together.
- **[Code structure](CODE_STRUCTURE.md)** — Where to find and change code in each part of the stack.
- **Component READMEs** — [Frontend](../frontend/README.md) · [Backend](../backend/README.md) · [MCP Server](../mcp-server/README.md).
