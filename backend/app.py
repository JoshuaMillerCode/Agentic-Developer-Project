"""
LLM Agent Backend — Phase 3.
Connects to the TMDB MCP Server, builds a ReAct agent with MCP tools,
and exposes /chat (with structured cards), discovery, and config for the frontend.
"""

import json
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from anthropic import AuthenticationError as AnthropicAuthenticationError

from langchain_mcp_adapters.sessions import StdioConnection, create_session
from langchain_mcp_adapters.tools import load_mcp_tools

from backend import tmdb_client
from backend.tmdb_client import TmdbClientError

# Load .env from project root (parent of backend/)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("backend")

# Config (env with safe defaults)
def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").strip()
    return [o.strip() for o in raw.split(",") if o.strip()]


CORS_ORIGINS = _cors_origins()
ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").strip().lower() in ("1", "true", "yes")
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))  # Messages API required; max output length
MCP_SERVER_SCRIPT_ENV = os.getenv("MCP_SERVER_SCRIPT", "").strip()
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "32000"))

# Discovery/configuration validation — align with MCP server (tmdb_tools).
DISCOVERY_MAX_PAGE = 500
DISCOVERY_MAX_LANGUAGE_LENGTH = 10
DISCOVERY_TIME_WINDOWS = ("day", "week")

# Anthropic model IDs: https://docs.anthropic.com/en/docs/about-claude/models and model-deprecations.
# Valid: claude-sonnet-4-6, claude-sonnet-4-5, claude-opus-4-6, claude-haiku-4-5, etc. Claude 3.5 Sonnet retired 2025-10-28.
ANTHROPIC_DEFAULT_MODEL = "claude-sonnet-4-6"


def _validate_discovery_params(page: int, language: str) -> None:
    """Raise HTTPException(400) if page or language invalid. Call at start of discovery routes."""
    if page < 1 or page > DISCOVERY_MAX_PAGE:
        raise HTTPException(
            status_code=400,
            detail=f"page must be between 1 and {DISCOVERY_MAX_PAGE}",
        )
    lang = (language or "").strip()
    if len(lang) > DISCOVERY_MAX_LANGUAGE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"language must be at most {DISCOVERY_MAX_LANGUAGE_LENGTH} characters",
        )


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=32_000, description="User message (max 32000 chars)")


# Card models for chat and discovery — frontend renders these as movie/TV/person cards.
class MovieCard(BaseModel):
    type: Literal["movie"] = "movie"
    id: int
    title: str | None = None
    poster_path: str | None = None
    release_date: str | None = None
    vote_average: float | None = None
    overview: str | None = None


class TVCard(BaseModel):
    type: Literal["tv"] = "tv"
    id: int
    name: str | None = None
    poster_path: str | None = None
    first_air_date: str | None = None
    vote_average: float | None = None
    overview: str | None = None


class PersonCard(BaseModel):
    type: Literal["person"] = "person"
    id: int
    name: str | None = None
    profile_path: str | None = None
    known_for_department: str | None = None
    known_for: list[str] = Field(default_factory=list)
    biography: str | None = None


Card = MovieCard | TVCard | PersonCard


def _item_to_movie_card(item: dict[str, Any]) -> MovieCard:
    """Build MovieCard from TMDb item. Callers must pass items with 'id' set."""
    return MovieCard(
        id=item.get("id", 0),
        title=item.get("title"),
        poster_path=item.get("poster_path"),
        release_date=item.get("release_date"),
        vote_average=item.get("vote_average"),
        overview=(item.get("overview") or "")[:500] or None,
    )


def _item_to_tv_card(item: dict[str, Any]) -> TVCard:
    return TVCard(
        id=item.get("id", 0),
        name=item.get("name"),
        poster_path=item.get("poster_path"),
        first_air_date=item.get("first_air_date"),
        vote_average=item.get("vote_average"),
        overview=(item.get("overview") or "")[:500] or None,
    )


def _item_to_person_card(item: dict[str, Any]) -> PersonCard:
    known_for_raw = item.get("known_for") or []
    known_for = []
    for k in known_for_raw:
        if isinstance(k, dict):
            known_for.append(k.get("title") or k.get("name") or "")
        elif isinstance(k, str):
            known_for.append(k)
    bio = item.get("biography") or ""
    return PersonCard(
        id=item.get("id", 0),
        name=item.get("name"),
        profile_path=item.get("profile_path"),
        known_for_department=item.get("known_for_department"),
        known_for=[t for t in known_for if t][:10],
        biography=bio[:500] if bio else None,
    )


def _parse_tool_content_to_cards(content: str) -> list[Card]:
    """Parse MCP tool JSON output into a list of Card models. Skips errors and non-list responses."""
    cards: list[Card] = []
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return cards
    if not isinstance(data, dict):
        return cards
    if "error" in data:
        return cards
    seen: set[tuple[str, int]] = set()

    def add_movie(item: dict[str, Any]) -> None:
        if not isinstance(item, dict) or not item.get("id"):
            return
        key = ("movie", item["id"])
        if key in seen:
            return
        seen.add(key)
        cards.append(_item_to_movie_card(item))

    def add_tv(item: dict[str, Any]) -> None:
        if not isinstance(item, dict) or not item.get("id"):
            return
        key = ("tv", item["id"])
        if key in seen:
            return
        seen.add(key)
        cards.append(_item_to_tv_card(item))

    def add_person(item: dict[str, Any]) -> None:
        if not isinstance(item, dict) or not item.get("id"):
            return
        key = ("person", item["id"])
        if key in seen:
            return
        seen.add(key)
        cards.append(_item_to_person_card(item))

    results = data.get("results")
    if isinstance(results, list):
        for r in results:
            if not isinstance(r, dict):
                continue
            if "title" in r and "release_date" in r:
                add_movie(r)
            elif "name" in r and ("first_air_date" in r or "original_name" in r):
                add_tv(r)
            elif "name" in r and ("known_for_department" in r or "profile_path" in r or "known_for" in r):
                add_person(r)
            elif "media_type" in r:
                if r.get("media_type") == "movie":
                    add_movie(r)
                elif r.get("media_type") == "tv":
                    add_tv(r)
                elif r.get("media_type") == "person":
                    add_person(r)
            else:
                if "title" in r:
                    add_movie(r)
                elif "first_air_date" in r:
                    add_tv(r)
                else:
                    add_person(r)
        return cards
    # Single object (e.g. get_movie_details)
    if "title" in data and "release_date" in data:
        add_movie(data)
    elif "name" in data and ("first_air_date" in data or "original_name" in data):
        add_tv(data)
    elif "name" in data and ("known_for_department" in data or "biography" in data):
        add_person(data)
    return cards


def _message_content_to_text(content: Any) -> str:
    """Safely get a string from message content (string or list of content blocks)."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        first = content[0] if content else None
        if first is None:
            return ""
        if isinstance(first, dict):
            return first.get("text", "") or ""
        if isinstance(first, str):
            return first
        return ""
    return ""


def extract_cards_from_agent_result(messages: list[Any]) -> list[Card]:
    """Collect all cards from tool results in the agent message list."""
    out: list[Card] = []
    seen: set[tuple[str, int]] = set()
    for m in messages:
        if not isinstance(m, ToolMessage):
            continue
        raw = _message_content_to_text(m.content)
        if not raw:
            continue
        for card in _parse_tool_content_to_cards(raw):
            key = (card.type, card.id)
            if key in seen:
                continue
            seen.add(key)
            out.append(card)
    return out


class ChatResponse(BaseModel):
    response: str
    reply_found: bool = True
    cards: list[MovieCard | TVCard | PersonCard] = Field(default_factory=list, description="Structured cards for inline rendering")


# System prompt: full tool map so the agent knows when to use each TMDB tool.
# Tools are discovered at startup from the MCP server; this prompt guides the LLM.
SYSTEM_PROMPT = """You are a helpful assistant with access to The Movie Database (TMDB). You have many tools; use them when relevant and answer in clear, friendly language. Do not make up data—only use what the tools return. If a tool returns an error (e.g. validation_error, rate_limit_exceeded), explain simply and suggest retrying or rephrasing.

## Tool map — use the right tool for the question

**Configuration**
- get_configuration — Image base URLs, languages, countries, timezones. Use when building poster/image URLs or needing locale data.

**Search (by name or title)**
- search_movie(query, page, language) — Find movies by title. Use when the user asks about a film or movie name.
- search_tv(query, page, language) — Find TV shows by title. Use when the user asks about a series or show name.
- search_person(query, page, language) — Find people (actors, directors, crew) by name. Use when the user asks about a person or wants to find someone's filmography.
- search_multi(query, page, language) — Search movies, TV, and people in one call. Use when the query could match any type (e.g. a title that exists as both movie and show).

**Discover & browse movies**
- discover_movie(sort_by, page, language, primary_release_year, vote_average_gte, vote_average_lte, with_genres, year) — Browse movies with filters (genre, year, rating, sort). Use for "movies from 2020", "best rated sci‑fi", etc.
- get_movie_now_playing(page, language) — Movies currently in theatres. Use for "what's in cinemas" or "now playing".
- get_movie_popular(page, language) — Popular movies (list). Use for "popular movies" or trending list.
- get_movie_top_rated(page, language) — Top rated movies. Use for "best movies" or "highest rated films".
- get_movie_upcoming(page, language) — Upcoming releases. Use for "what's coming soon" or "new movies".

**Trending**
- get_trending_movies(time_window) — time_window: 'day' or 'week'. Use for "trending movies" or "hot movies now".
- get_trending_tv(time_window) — Trending TV shows (day or week). Use for "trending TV" or "hot shows".
- get_trending_all(time_window) — All trending content (movies, TV, people) in one list. Use for "what's trending" in general.
- get_trending_people(time_window) — Trending people (actors, etc.). Use for "who's trending" or "popular actors right now".

**Browse TV**
- get_tv_airing_today(page, language) — Shows airing today. Use for "what's on TV today".
- get_tv_on_the_air(page, language) — Shows currently on the air (this season). Use for "currently running series".
- get_tv_popular(page, language) — Popular TV shows. Use for "popular series".
- get_tv_top_rated(page, language) — Top rated TV shows. Use for "best shows" or "highest rated series".

**Movie & TV details (by ID — get ID from search first)**
- get_movie_details(movie_id) — Full movie info (overview, cast, etc.). Use after search_movie when the user wants more than a list.
- get_tv_details(tv_id) — Full TV show info (overview, seasons, etc.). Use after search_tv when the user wants more than a list.
- get_tv_season_details(tv_id, season_number, language) — A specific season (episode list, etc.). season_number is 1-based; 0 for specials. Use when the user asks about a season.
- get_tv_episode_details(tv_id, season_number, episode_number, language) — A specific episode. Use when the user asks about an episode (e.g. S01E05).

**Credits (cast & crew)**
- get_movie_credits(movie_id) — Cast and crew for a movie. Use when the user asks "who's in this film" or for a movie's cast list.
- get_tv_credits(tv_id) — Cast and crew for a TV show. Use when the user asks who's in a series or for a show's cast list.

**People (by person_id — get ID from search_person first)**
- get_person_details(person_id) — Full person info (bio, birthday, etc.). Use after search_person when the user wants more than a name.
- get_person_movie_credits(person_id) — Movie credits for a person. Use when the user asks what movies an actor or crew member has been in.
- get_person_tv_credits(person_id) — TV credits for a person. Use when the user asks what TV shows an actor or crew member has been in.

**Workflow tips**
- For "find movie X" or "movie named Y": search_movie then optionally get_movie_details or get_movie_credits.
- For "find show X" or "TV series Y": search_tv then optionally get_tv_details, get_tv_season_details, get_tv_episode_details, or get_tv_credits.
- For "who is X" or "actor Y": search_person then optionally get_person_details, get_person_movie_credits, get_person_tv_credits.
- When the user's query is ambiguous (e.g. a title that could be movie or TV), search_multi can return all types."""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start MCP session to TMDB server, load tools, build agent. Keep session for app lifetime."""
    project_root = Path(__file__).resolve().parent.parent
    if MCP_SERVER_SCRIPT_ENV:
        server_script = Path(MCP_SERVER_SCRIPT_ENV)
        if not server_script.is_absolute():
            server_script = (project_root / server_script).resolve()
    else:
        server_script = project_root / "mcp-server" / "server.py"
    if not server_script.exists():
        raise RuntimeError(
            f"MCP server script not found: {server_script}. Set MCP_SERVER_SCRIPT or run from project root."
        )

    # Optional: fail fast if TMDB key missing (first tool use would fail otherwise)
    if not (os.environ.get("TMDB_API_KEY") or "").strip():
        logger.warning("TMDB_API_KEY is not set; MCP tools that call TMDB will fail until it is set.")

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

        # Prefer Anthropic when both keys are set
        # LangChain ChatAnthropic maps to Messages API: model, max_tokens, messages (+ system via agent prompt)
        if anthropic_key and anthropic_key.strip():
            from langchain_anthropic import ChatAnthropic
            model = ChatAnthropic(
                api_key=anthropic_key.strip(),
                model=os.environ.get("ANTHROPIC_MODEL", ANTHROPIC_DEFAULT_MODEL),
                max_tokens=LLM_MAX_TOKENS,
                temperature=0,
                timeout=LLM_TIMEOUT_SECONDS,
                max_retries=0,
            )
        elif api_key and api_key.strip():
            model = ChatOpenAI(
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0,
                timeout=LLM_TIMEOUT_SECONDS,
                max_retries=0,
            )
        else:
            raise RuntimeError(
                "Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env (see .env.example)."
            )

        agent = create_react_agent(
            model=model,
            tools=tools,
            prompt=SYSTEM_PROMPT,
        )
        # create_react_agent returns an already-compiled graph (CompiledStateGraph)
        app.state.agent = agent
        app.state.tools = tools
        yield
    # Session closed on exit


def create_app(lifespan_fn=None):
    """Build the FastAPI app. Optional lifespan_fn for testing (no MCP/LLM)."""
    app = FastAPI(
        title="Agentic Developer — LLM Agent Backend",
        description="Chat endpoint that uses TMDB MCP tools via a ReAct agent.",
        lifespan=lifespan_fn or lifespan,
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s %s %.0fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
        allow_credentials=ALLOW_CREDENTIALS if CORS_ORIGINS else False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health(request: Request):
        agent = getattr(request.app.state, "agent", None)
        if agent is None:
            raise HTTPException(status_code=503, detail="Agent not ready")
        return {"status": "ok"}

    @app.get("/configuration")
    async def get_config(request: Request):
        """TMDb API configuration (image base URLs) for building poster/photo URLs."""
        try:
            config = tmdb_client.get_configuration()
        except RuntimeError as e:
            if "TMDB_API_KEY" in str(e):
                raise HTTPException(status_code=503, detail="TMDb not configured")
            raise HTTPException(status_code=502, detail="Configuration unavailable")
        except TmdbClientError as e:
            logger.warning("Configuration request failed: %s", e)
            raise HTTPException(status_code=502, detail="Configuration unavailable")
        except Exception:
            logger.exception("Configuration request failed")
            raise HTTPException(status_code=502, detail="Configuration unavailable")
        return config

    @app.get("/discovery/movies/popular")
    async def discovery_movies_popular(page: int = 1, language: str = "en-US"):
        """Currently popular movies — for discovery section."""
        _validate_discovery_params(page, language)
        try:
            data = tmdb_client.get_movie_popular(page=page, language=language)
        except RuntimeError:
            raise HTTPException(status_code=503, detail="TMDb not configured")
        except TmdbClientError as e:
            logger.warning("Discovery movies/popular failed: %s", e)
            raise HTTPException(status_code=502, detail="Discovery unavailable")
        except Exception:
            logger.exception("Discovery movies/popular failed")
            raise HTTPException(status_code=502, detail="Discovery unavailable")
        results = data.get("results") or []
        cards = [_item_to_movie_card(r) for r in results if isinstance(r, dict) and r.get("id")]
        return {"results": cards, "page": data.get("page", 1), "total_pages": data.get("total_pages", 0), "total_results": data.get("total_results", 0)}

    @app.get("/discovery/movies/now-playing")
    async def discovery_movies_now_playing(page: int = 1, language: str = "en-US"):
        """Movies now playing in theatres — for discovery section."""
        _validate_discovery_params(page, language)
        try:
            data = tmdb_client.get_movie_now_playing(page=page, language=language)
        except RuntimeError:
            raise HTTPException(status_code=503, detail="TMDb not configured")
        except TmdbClientError as e:
            logger.warning("Discovery movies/now-playing failed: %s", e)
            raise HTTPException(status_code=502, detail="Discovery unavailable")
        except Exception:
            logger.exception("Discovery movies/now-playing failed")
            raise HTTPException(status_code=502, detail="Discovery unavailable")
        results = data.get("results") or []
        cards = [_item_to_movie_card(r) for r in results if isinstance(r, dict) and r.get("id")]
        return {"results": cards, "page": data.get("page", 1), "total_pages": data.get("total_pages", 0), "total_results": data.get("total_results", 0)}

    @app.get("/discovery/tv/popular")
    async def discovery_tv_popular(page: int = 1, language: str = "en-US"):
        """Popular TV series — for discovery section."""
        _validate_discovery_params(page, language)
        try:
            data = tmdb_client.get_tv_popular(page=page, language=language)
        except RuntimeError:
            raise HTTPException(status_code=503, detail="TMDb not configured")
        except TmdbClientError as e:
            logger.warning("Discovery tv/popular failed: %s", e)
            raise HTTPException(status_code=502, detail="Discovery unavailable")
        except Exception:
            logger.exception("Discovery tv/popular failed")
            raise HTTPException(status_code=502, detail="Discovery unavailable")
        results = data.get("results") or []
        cards = [_item_to_tv_card(r) for r in results if isinstance(r, dict) and r.get("id")]
        return {"results": cards, "page": data.get("page", 1), "total_pages": data.get("total_pages", 0), "total_results": data.get("total_results", 0)}

    @app.get("/discovery/people/trending")
    async def discovery_people_trending(time_window: str = "day", page: int = 1):
        """Trending people (actors, etc.) — for discovery section. time_window: day | week."""
        tw = (time_window or "day").strip().lower()
        if tw not in DISCOVERY_TIME_WINDOWS:
            raise HTTPException(
                status_code=400,
                detail="time_window must be 'day' or 'week'",
            )
        _validate_discovery_params(page, "")
        try:
            data = tmdb_client.get_trending_people(time_window=tw, page=page)
        except RuntimeError:
            raise HTTPException(status_code=503, detail="TMDb not configured")
        except TmdbClientError as e:
            logger.warning("Discovery people/trending failed: %s", e)
            raise HTTPException(status_code=502, detail="Discovery unavailable")
        except Exception:
            logger.exception("Discovery people/trending failed")
            raise HTTPException(status_code=502, detail="Discovery unavailable")
        results = data.get("results") or []
        cards = [_item_to_person_card(r) for r in results if isinstance(r, dict) and r.get("id")]
        return {"results": cards, "page": data.get("page", 1), "total_pages": data.get("total_pages", 0), "total_results": data.get("total_results", 0)}

    @app.post("/chat", response_model=ChatResponse)
    async def chat(body: ChatRequest, request: Request):
        logger.info("chat request body: %s", body)
        message = (body.message or "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="message is required")

        agent = getattr(request.app.state, "agent", None)
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not ready")

        try:
            result = await agent.ainvoke({"messages": [HumanMessage(content=message)]})
            messages = result.get("messages") or []
            cards = extract_cards_from_agent_result(messages)
            for m in reversed(messages):
                if hasattr(m, "content") and m.content:
                    text = _message_content_to_text(m.content)
                    if text:
                        return ChatResponse(response=text, reply_found=True, cards=cards)
            return ChatResponse(
                response="I couldn't generate a reply. Please try again.",
                reply_found=False,
                cards=cards,
            )
        except AnthropicAuthenticationError as e:
            logger.warning("Anthropic authentication failed: %s", e)
            raise HTTPException(
                status_code=401,
                detail="Invalid API key. Check ANTHROPIC_API_KEY in .env.",
            )
        except Exception as e:
            # Anthropic (and other providers) may return 400 for billing/auth (e.g. low credits)
            if type(e).__name__ == "BadRequestError" and "anthropic" in type(e).__module__:
                err_detail = getattr(e, "message", None) or getattr(e, "body", None) or str(e)
                logger.warning(
                    "Anthropic API error (e.g. billing or invalid request): %s (full: %r)",
                    err_detail,
                    e,
                )
                raise HTTPException(
                    status_code=502,
                    detail="The AI service could not process your request. Please try again later or check your API account.",
                )
            logger.exception("Chat request failed")
            raise HTTPException(
                status_code=500,
                detail="An error occurred while processing your request.",
            )

    return app


app = create_app()
