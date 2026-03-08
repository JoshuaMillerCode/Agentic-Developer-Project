"""
LLM Agent Backend — Phase 3.
Connects to the TMDB MCP Server, builds a ReAct agent with MCP tools,
and exposes /chat for the frontend.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

from langchain_mcp_adapters.sessions import StdioConnection, create_session
from langchain_mcp_adapters.tools import load_mcp_tools

# Load .env from project root (parent of backend/)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


# System prompt: when to use which tools (TMDB movie/TV)
SYSTEM_PROMPT = """You are a helpful assistant with access to The Movie Database (TMDB). You can search and discover movies and TV shows, get details, and see what's trending.

Use the tools when the user asks about:
- A specific movie or film title → search_movie or get_movie_details
- A specific TV show or series → search_tv or get_tv_details
- What's popular, trending, or hot now → get_trending_movies or get_trending_tv
- Browsing movies by genre, year, or rating → discover_movie
- Building image URLs or needing API configuration → get_configuration

When you use a tool, interpret the JSON result and answer in clear, friendly language. If a tool returns an error (e.g. validation_error, rate_limit_exceeded), explain it simply to the user and suggest retrying or rephrasing. Do not make up movie or TV data; only use what the tools return."""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start MCP session to TMDB server, load tools, build agent. Keep session for app lifetime."""
    project_root = Path(__file__).resolve().parent.parent
    server_script = project_root / "mcp-server" / "server.py"
    if not server_script.exists():
        raise RuntimeError(
            f"MCP server script not found: {server_script}. Run from project root."
        )

    connection: StdioConnection = {
        "transport": "stdio",
        "command": "python",
        "args": [str(server_script)],
        "cwd": str(project_root),
        "env": dict(os.environ),
    }

    async with create_session(connection) as session:
        await session.initialize()
        tools = await load_mcp_tools(session)
        if not tools:
            raise RuntimeError("No tools loaded from MCP server.")

        api_key = os.environ.get("OPENAI_API_KEY")
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        if not (api_key and api_key.strip()) and not (anthropic_key and anthropic_key.strip()):
            raise RuntimeError(
                "Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env (see .env.example)."
            )

        if api_key and api_key.strip():
            model = ChatOpenAI(
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0,
            )
        else:
            try:
                from langchain_anthropic import ChatAnthropic
                model = ChatAnthropic(
                    model=os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
                    temperature=0,
                )
            except ImportError:
                raise RuntimeError(
                    "ANTHROPIC_API_KEY set but langchain-anthropic not installed. "
                    "Install with: pip install langchain-anthropic"
                )

        agent = create_react_agent(
            model=model,
            tools=tools,
            prompt=SYSTEM_PROMPT,
        )
        app.state.agent = agent.compile()
        app.state.tools = tools
        yield
    # Session closed on exit


app = FastAPI(
    title="Agentic Developer — LLM Agent Backend",
    description="Chat endpoint that uses TMDB MCP tools via a ReAct agent.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    """Run the agent on the user message and return the final text response."""
    message = (body.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    agent = getattr(app.state, "agent", None)
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not ready")

    try:
        result = await agent.ainvoke({"messages": [HumanMessage(content=message)]})
        messages = result.get("messages") or []
        # Last message is the assistant's final reply
        for m in reversed(messages):
            if hasattr(m, "content") and m.content:
                text = m.content if isinstance(m.content, str) else (
                    m.content[0].get("text", "") if isinstance(m.content, list) else ""
                )
                if text:
                    return {"response": text}
        return {"response": "I couldn't generate a reply. Please try again."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
