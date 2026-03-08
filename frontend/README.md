# Reel Recs — Frontend

Next.js web UI for the Agentic Developer project. **Reel Recs** is an AI-powered movie and TV recommendation app: users ask in plain English and get answers with inline movie, TV, and person cards. Dark theme, hero chat at the top, and scrollable discovery rows below.

**Tech:** Next.js 14 (App Router), TypeScript, Tailwind CSS. All data comes from the **LLM Agent Backend** — no API keys on the client.

---

## Prerequisites

- **Node.js** (LTS; see `package.json` for supported versions)
- **Backend** must be running before the frontend (see [Quick start](#quick-start))

---

## Quick start

**Run order:** Backend first, then frontend.

1. **Start the backend** (from project root):

   ```bash
   source .venv/bin/activate
   set -a && source .env 2>/dev/null || true; set +a
   python -m backend
   ```

   Backend: `http://localhost:8000`

2. **Start the frontend** (from project root or `frontend/`):

   ```bash
   cd frontend
   npm install   # first time only
   npm run dev
   ```

   App: `http://localhost:3000`

---

## Environment

Optional. Create `frontend/.env.local` (see `frontend/.env.local.example`) to override the backend URL:

| Variable | Description | Default |
|----------|-------------|--------|
| `NEXT_PUBLIC_API_URL` | Backend base URL for all API calls | `http://localhost:8000` |

No API keys are set in the frontend; the backend holds credentials and talks to external services.

---

## Project structure

| Path | Purpose |
|------|---------|
| `src/app/` | App Router: root layout, home page, and detail routes (`movie/[id]`, `tv/[id]`, `person/[id]`) |
| `src/components/chat/` | Hero chat input, AI response area, inline cards, and film-strip loading state |
| `src/components/discovery/` | Four scrollable discovery rows and the country/region filter |
| `src/components/cards/` | Shared card components (Movie, TV, Person) and `CardRenderer` used by chat and discovery |
| `src/lib/api.ts` | API client: config, chat, discovery, and detail endpoints; `buildImageUrl` for poster/profile URLs |
| `src/lib/types.ts` | TypeScript types for cards, API responses, and TMDb config |

---

## Main features

- **Hero chat** — Prominent search-style input at the top; user types a question and gets an AI reply with optional inline movie/TV/person cards. Last response is kept in session storage.
- **Discovery section** — Four horizontal scrollable rows: Currently Popular Movies, Now Playing in Theaters, Popular TV Series, Trending Actors. Uses the same card components in compact size.
- **Country/region filter** — Header dropdown (e.g. US, GB, All regions). Applies to discovery data and to the chat request so the AI can tailor recommendations.
- **Detail pages** — Clicking a card goes to `/movie/[id]`, `/tv/[id]`, or `/person/[id]` for full details (poster, overview, cast, etc.).
- **Loading state** — While the AI is thinking, a film-strip animation and “Searching the vault…” copy are shown.

---

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Development server (port 3000) |
| `npm run build` | Production build |
| `npm run start` | Run production build |
| `npm run lint` | ESLint |

---

## How it fits with the backend

- **Single API origin** — The frontend calls only `NEXT_PUBLIC_API_URL` (e.g. `http://localhost:8000`). The backend must allow this origin in CORS when running locally or from another host.
- **No keys on client** — All third-party and LLM API keys live in the backend environment. The frontend never sees or sends them.
- **Endpoints used** — Configuration (`/configuration`), chat (`POST /chat`), discovery (`/discovery/movies/popular`, `/discovery/movies/now-playing`, `/discovery/tv/popular`, `/discovery/people/trending`), and detail pages (`/movies/:id`, `/tv/:id`, `/people/:id`).

For backend setup, run order, and env vars, see the project root **README** and **backend/README.md**.
