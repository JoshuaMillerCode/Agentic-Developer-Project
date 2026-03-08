# Agentic Developer Project — Execution Plan

This document is the master plan to execute the **AI Builder Candidate Project: Agentic Web App with API Wrapper** as specified in the project brief. It breaks down every requirement and maps it to concrete tasks.

---

## 1. Document Summary (What We're Building)

**Goal:** Demonstrate end-to-end development of a modern, **agent-driven** application by:

1. Choosing a **public third-party REST API** (free access).
2. Building an **MCP Server wrapper** that exposes the API’s core functions.
3. Implementing an **LLM Agent backend** (LangChain or similar) with **tool/function calling** against the MCP Server.
4. Delivering a **web frontend** where users interact with the agent and see meaningful results.

**Constraints:**

- Must be built in a **true agentic IDE** (Cursor or GitHub Copilot Chat). Replit, V0, Bolt.new are **not** acceptable.
- The solution **does not need to be hosted live**.

---

## 2. Architecture Overview (Target State)

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  Frontend Web   │────▶│  LLM Agent Backend   │────▶│  MCP Server     │
│  App (UI)       │     │  (LangChain + tools)  │     │  (API Wrapper)   │
└─────────────────┘     └──────────────────────┘     └────────┬────────┘
         │                            │                        │
         │                            │                        ▼
         │                            │               ┌─────────────────┐
         │                            │               │  Public REST    │
         │                            │               │  API (3rd party)│
         └────────────────────────────┘               └─────────────────┘
```

- **Separation of concerns:** Frontend | Agent/Backend | MCP Server | External API.
- **Security:** API keys (third-party + LLM) handled via env/config, never in repo.

---

## 3. Phase-by-Phase Execution Plan

### Phase 1: Foundation & API Selection

| # | Task | Details | Done |
|---|------|---------|------|
| 1.1 | **Choose public REST API** | Pick one with free keys: e.g. Weather (OpenWeather), Jokes (e.g. JokeAPI), Facts (e.g. Numbers API), or other public data API. Document choice in README. | ☑ |
| 1.2 | **Obtain API key** | Register and get key; document where to get it and how to set it (e.g. `.env`). | ☑ |
| 1.3 | **Define repo structure** | Create clearly separated folders: `frontend/`, `backend/` (or `agent/`), `mcp-server/`. Add `.gitignore` (env, keys, node_modules, venv, etc.). | ☑ |
| 1.4 | **Dependency files** | Add `requirements.txt` (Python) and/or `package.json` (Node.js) with pinned versions for MCP server, backend, and frontend. | ☑ |

---

### Phase 2: MCP Server (API Wrapper)

| # | Task | Details | Done |
|---|------|---------|------|
| 2.1 | **Implement MCP Server** | Microservice that wraps the chosen REST API. Expose core operations as MCP tools/resources (e.g. “get weather”, “get joke”, “get fact”). | ☑ |
| 2.2 | **Tool/resource definitions** | Clear schema for each tool: name, description, parameters. Ensure the LLM can discover and call them. | ☑ |
| 2.3 | **API key handling** | MCP server reads third-party API key from environment (or config); never hardcode. Document in README. | ☑ |
| 2.4 | **Run instructions** | Document how to start the MCP server (port, env vars) so the agent backend can connect. | ☑ |

---

### Phase 3: LLM Agent Backend

| # | Task | Details | Done |
|---|------|---------|------|
| 3.1 | **Choose framework** | LangChain (or equivalent) with support for tool/function calling. Set up project and dependencies. | ☑ |
| 3.2 | **Connect to MCP Server** | Agent backend connects to the MCP Server (e.g. stdio or HTTP transport) and discovers tools. | ☑ |
| 3.3 | **Define tools in agent** | Map MCP tools to LangChain tools/functions so the LLM can invoke them (correct names, descriptions, parameters). | ☑ |
| 3.4 | **Prompt design** | System/user prompts that make the agent contextually use the right tool (e.g. “answer using weather when relevant”). | ☑ |
| 3.5 | **LLM API key** | Use env/config for LLM provider key (e.g. OpenAI, Anthropic). Document in README. | ☑ |
| 3.6 | **API for frontend** | Expose an HTTP API (e.g. `/chat` or `/query`) that the frontend calls; backend runs the agent and returns responses. | ☑ |

---

### Phase 4: Frontend Web App

| # | Task | Details | Done |
|---|------|---------|------|
| 4.1 | **Simple UI** | Build a minimal web app: input (e.g. text box), send button, and area to show agent responses. | ☑ |
| 4.2 | **Call backend** | Frontend calls the agent backend API and displays returned text (or structured data). | ☑ |
| 4.3 | **End-to-end flow** | User question → backend → agent chooses tools → MCP Server → external API → response back to UI. Verify full path. | ☐ |

---

### Phase 5: Documentation & Repo Readiness

| # | Task | Details | Done |
|---|------|---------|------|
| 5.1 | **README.md** | Clear instructions: env setup, how to get third-party and LLM API keys, how to start MCP Server, how to run backend and frontend. | ☐ |
| 5.2 | **Code structure section** | In README, describe folders: frontend, LLM backend/agent, MCP Server wrapper. | ☐ |
| 5.3 | **Dependencies** | requirements.txt and/or package.json with all libraries and versions. | ☐ |
| 5.4 | **Documentation philosophy** | Brief note (for video/docs) on how a new or collaborating developer would onboard (README, env, architecture, key flows). | ☐ |

---

### Phase 6: Video Demonstration (Screen Recording)

| # | Task | Details | Done |
|---|------|---------|------|
| 6.1 | **Recording setup** | Use ScreenRec or similar; **candidate on camera** during the presentation. | ☐ |
| 6.2 | **Approach & prompts** | Clearly describe development approach and **show the prompts** used in the agentic IDE to build: MCP wrapper, tool/function definitions, frontend structure. | ☐ |
| 6.3 | **Content coverage** | Ensure the video covers: | ☐ |
|     | (a) | Selected API and its core function. | ☐ |
|     | (b) | MCP Server architecture and benefits. | ☐ |
|     | (c) | LLM Agent setup: tool definitions, prompt structure, LangChain logic. | ☐ |
|     | (d) | End-to-end user experience in the web app. | ☐ |
|     | (e) | **Deployment:** Verbal overview (e.g. Docker, Kubernetes, serverless). | ☐ |
|     | (f) | **Documentation:** Overview of documentation philosophy for a collaborator or new developer taking over. | ☐ |

---

## 4. Evaluation Criteria Checklist (Align Work to Grading)

| Category | Weight | How to Address |
|----------|--------|----------------|
| **Agentic Development** | 30% | Use Cursor (or Copilot Chat) effectively; save/share representative prompts; show iterative, prompt-driven development. |
| **Architectural Design** | 30% | Clean MCP wrapper design, clear separation (frontend / agent / MCP / API), secure API key handling. |
| **LLM & Tooling** | 20% | Correct tool calling (LangChain or equivalent), contextual answers, clear prompt engineering. |
| **Presentation & Documentation** | 20% | Professional video, full coverage of deployment and documentation, technically accurate narration. |

---

## 5. Suggested Order of Execution

1. **Phase 1** — Repo structure, API choice, dependency files.  
2. **Phase 2** — MCP Server implementation and run instructions.  
3. **Phase 3** — LLM Agent backend with MCP tools and prompts.  
4. **Phase 4** — Frontend and end-to-end testing.  
5. **Phase 5** — README and documentation.  
6. **Phase 6** — Script and record video; optionally add deployment notes to README for the verbal deployment discussion.

---

## 6. Quick Reference: Deliverables

- [ ] **Video:** Screen recording with candidate on camera; approach, prompts, API, MCP, agent, UX, deployment, documentation.
- [ ] **Repo:** GitHub/GitLab link with README, dependency files, and clear folders: frontend, LLM backend/agent, MCP Server wrapper.

---

*Generated from the project brief: Agentic Web App with API Wrapper (AI Builder Candidate Project).*
