"""
LLM Agent Backend — Phase 3.
Connects to the TMDB MCP Server, builds a ReAct agent with MCP tools,
and exposes /chat (with structured cards), discovery, and config for the frontend.
"""

import json
import logging
import os
import re
import time
import asyncio
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

from anthropic import AuthenticationError as AnthropicAuthenticationError, RateLimitError

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


def _validate_region(region: str | None) -> str | None:
    """Return normalized 2-letter uppercase region or None. Raise HTTPException(400) if invalid."""
    if region is None or not (region := region.strip()):
        return None
    if len(region) != 2 or not region.isalpha():
        raise HTTPException(
            status_code=400,
            detail="region must be a 2-letter ISO 3166-1 country code (e.g. US, GB)",
        )
    return region.upper()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=32_000, description="User message (max 32000 chars)")
    region: str | None = Field(None, max_length=2, description="Optional ISO 3166-1 country code to filter content (e.g. US)")


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


# Movie detail page: full movie info + cast (for GET /movies/{movie_id})
class CastMember(BaseModel):
    id: int
    name: str | None = None
    character: str | None = None
    profile_path: str | None = None


class MovieDetailResponse(BaseModel):
    """Movie show page: card fields plus tagline, genres, runtime, cast."""
    type: Literal["movie"] = "movie"
    id: int
    title: str | None = None
    poster_path: str | None = None
    release_date: str | None = None
    vote_average: float | None = None
    overview: str | None = None
    tagline: str | None = None
    genres: list[dict[str, Any]] = Field(default_factory=list)
    runtime: int | None = None
    cast: list[CastMember] = Field(default_factory=list)


# Person detail page (GET /people/{person_id})
class PersonDetailResponse(BaseModel):
    type: Literal["person"] = "person"
    id: int
    name: str | None = None
    profile_path: str | None = None
    known_for_department: str | None = None
    known_for: list[str] = Field(default_factory=list)
    biography: str | None = None
    birthday: str | None = None
    place_of_birth: str | None = None
    movie_credits: list[dict[str, Any]] = Field(default_factory=list)
    tv_credits: list[dict[str, Any]] = Field(default_factory=list)


# TV detail page (GET /tv/{tv_id})
class TvDetailResponse(BaseModel):
    type: Literal["tv"] = "tv"
    id: int
    name: str | None = None
    poster_path: str | None = None
    first_air_date: str | None = None
    vote_average: float | None = None
    overview: str | None = None
    tagline: str | None = None
    genres: list[dict[str, Any]] = Field(default_factory=list)
    number_of_seasons: int | None = None
    cast: list[CastMember] = Field(default_factory=list)


# Tool names that can contribute cards. Includes search/details/credits AND discovery/trending/list
# so that broad queries (e.g. "family movie night") get candidates from discover_movie, get_movie_top_rated, etc.
# We still filter by "mentioned in response" so only titles the AI actually says are returned.
TOOLS_FOR_CHAT_CARDS = frozenset({
    "search_movie", "search_tv", "search_person", "search_multi",
    "get_movie_details", "get_tv_details", "get_person_details",
    "get_movie_credits", "get_tv_credits", "get_person_movie_credits", "get_person_tv_credits",
    "discover_movie",
    "get_movie_now_playing", "get_movie_popular", "get_movie_top_rated", "get_movie_upcoming",
    "get_trending_movies", "get_trending_tv", "get_trending_all", "get_trending_people",
    "get_tv_airing_today", "get_tv_on_the_air", "get_tv_popular", "get_tv_top_rated",
})
# Max cards returned in one chat response (avoids huge lists from full filmography/credits).
CHAT_CARDS_MAX = int(os.getenv("CHAT_CARDS_MAX", "24"))
# Max cards to collect from tools before filtering by response (so we have enough to match).
CHAT_CARDS_CANDIDATE_MAX = int(os.getenv("CHAT_CARDS_CANDIDATE_MAX", "200"))


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

    # Credits responses: cast/crew arrays (get_person_movie_credits, get_movie_credits, etc.)
    for key in ("cast", "crew"):
        cred_list = data.get(key)
        if not isinstance(cred_list, list):
            continue
        for r in cred_list:
            if not isinstance(r, dict) or not r.get("id"):
                continue
            # Cast/crew item can be a movie (id, title, release_date) or person (id, name, character/profile_path)
            if "title" in r and ("release_date" in r or "character" in r):
                add_movie(r)
            elif "name" in r and ("character" in r or "profile_path" in r or "job" in r):
                add_person(r)

    results = data.get("results")
    if isinstance(results, list):
        for r in results:
            if not isinstance(r, dict):
                continue
            # Prefer media_type when present (e.g. search_multi, trending_all)
            if "media_type" in r:
                if r.get("media_type") == "movie":
                    add_movie(r)
                elif r.get("media_type") == "tv":
                    add_tv(r)
                elif r.get("media_type") == "person":
                    add_person(r)
                continue
            # Person before TV: person objects can have "original_name" (localized), which would wrongly match TV
            if "name" in r and ("known_for_department" in r or "profile_path" in r or "known_for" in r):
                add_person(r)
            elif "title" in r and "release_date" in r:
                add_movie(r)
            elif "name" in r and ("first_air_date" in r or "original_name" in r):
                add_tv(r)
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


def _card_display_name(card: Card) -> str | None:
    """Return the name/title used for display and for matching against response text."""
    if isinstance(card, MovieCard):
        return card.title
    if isinstance(card, TVCard):
        return card.name
    if isinstance(card, PersonCard):
        return card.name
    return None


def _filter_cards_mentioned_in_response(cards: list[Card], response_text: str) -> list[Card]:
    """
    Return cards whose title/name appears in the AI response, in order of first mention.
    Uses word-boundary and title-like context so generic words (e.g. "Boxing" the movie)
    don't match prose like "boxing movies" or "female boxer".
    """
    if not response_text or not cards:
        return []
    text_lower = response_text.lower()
    # Title-like suffix: after the title we expect " (year)", "**", ":", or end/newline (list context)
    title_like_suffix_re = re.compile(r"^\s*(\(\d{4}\)|\*\*|:|\n|$)")

    def _is_title_like_match(name: str, pos: int) -> bool:
        """True if the occurrence at pos looks like a listed title, not prose."""
        if not name or pos < 0:
            return False
        end = pos + len(name)
        if end > len(text_lower):
            return False
        # Word boundary: char before (if any) and after (if any) must not be alphanumeric
        if pos > 0 and text_lower[pos - 1].isalnum():
            return False
        if end < len(text_lower) and text_lower[end].isalnum():
            return False
        # For short single-word titles, require title-like context after (avoids "boxing" in "boxing movies")
        name_clean = name.strip()
        if len(name_clean) <= 12 and " " not in name_clean:
            rest = text_lower[end:]
            if not rest or not title_like_suffix_re.match(rest):
                return False
        return True

    found: list[tuple[int, Card]] = []
    for card in cards:
        name = _card_display_name(card)
        if not name or not name.strip():
            continue
        name_clean = name.strip()
        if " (" in name_clean and name_clean.endswith(")"):
            name_clean = name_clean.split(" (")[0].strip()
        if not name_clean:
            continue
        name_lower = name_clean.lower()
        pos = 0
        while True:
            pos = text_lower.find(name_lower, pos)
            if pos == -1:
                alt = name_clean.replace("+", "&")
                if alt != name_clean:
                    pos = text_lower.find(alt.lower())
                break
            if _is_title_like_match(name_lower, pos):
                found.append((pos, card))
                break
            pos += 1
    found.sort(key=lambda x: x[0])
    return [c for _, c in found]


def extract_cards_from_agent_result(messages: list[Any]) -> list[Card]:
    """Collect cards from all relevant tool results (search, details, credits, discovery, trending)."""
    out: list[Card] = []
    seen: set[tuple[str, int]] = set()
    for m in messages:
        if not isinstance(m, ToolMessage):
            continue
        tool_name = getattr(m, "name", None)
        if tool_name not in TOOLS_FOR_CHAT_CARDS:
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
            if len(out) >= CHAT_CARDS_CANDIDATE_MAX:
                break
        if len(out) >= CHAT_CARDS_CANDIDATE_MAX:
            break
    return out


class ChatResponse(BaseModel):
    response: str
    reply_found: bool = True
    cards: list[MovieCard | TVCard | PersonCard] = Field(default_factory=list, description="Structured cards for inline rendering")


# System prompt: keep short to reduce input tokens (rate limits). Tool names/descriptions come from MCP.
SYSTEM_PROMPT = """You are a helpful assistant with access to The Movie Database (TMDB). Use the available tools when relevant and answer in clear, friendly language. Do not make up data—only use what the tools return. If a tool returns an error (e.g. validation_error, rate_limit_exceeded), explain briefly and suggest retrying or rephrasing.

Strategy: Use search_movie, search_tv, or search_person for names/titles; search_multi when a query could match movie or TV. Use get_movie_details, get_tv_details, get_person_details and get_*_credits for deeper info after search. Use discover_movie, get_movie_popular, get_tv_popular, get_trending_* for browsing (e.g. "popular movies", "trending this week"). Get IDs from search or list results before calling detail/credit tools.

Critical—minimize tool calls: You have a strict limit on how many times you can call tools. For genre or theme requests (e.g. "boxing movies", "fighting movies", "romantic comedies"), use exactly ONE call: either one discover_movie with with_genres, or one search_movie with a single broad query (e.g. "boxing"). Then answer immediately using only those results. Do not call discover_movie twice, and do not call search_movie for individual titles (Rocky, Creed, etc.). One discover or one search, then respond."""


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
            # Prompt caching: cached tokens don't count toward 30K input tokens/min (per Anthropic rate limits).
            # Enables ephemeral cache so system prompt + tool context can be reused; set ANTHROPIC_PROMPT_CACHING=false to disable.
            if os.environ.get("ANTHROPIC_PROMPT_CACHING", "true").strip().lower() in ("1", "true", "yes"):
                model = model.bind(cache_control={"type": "ephemeral"})
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
    async def discovery_movies_popular(page: int = 1, language: str = "en-US", region: str | None = None):
        """Currently popular movies — for discovery section. region: optional 2-letter country (e.g. US)."""
        _validate_discovery_params(page, language)
        region_val = _validate_region(region) if region else None
        try:
            data = tmdb_client.get_movie_popular(page=page, language=language, region=region_val)
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
    async def discovery_movies_now_playing(page: int = 1, language: str = "en-US", region: str | None = None):
        """Movies now playing in theatres — for discovery section. region: optional 2-letter country (e.g. US)."""
        _validate_discovery_params(page, language)
        region_val = _validate_region(region) if region else None
        try:
            data = tmdb_client.get_movie_now_playing(page=page, language=language, region=region_val)
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

    @app.get("/movies/{movie_id}", response_model=MovieDetailResponse)
    async def get_movie_detail(movie_id: int, language: str = "en-US"):
        """Movie show/detail page: full movie info plus cast. Used when user clicks a movie card."""
        if movie_id < 1:
            raise HTTPException(status_code=400, detail="movie_id must be a positive integer")
        lang = (language or "en-US").strip()
        if len(lang) > DISCOVERY_MAX_LANGUAGE_LENGTH:
            raise HTTPException(status_code=400, detail=f"language must be at most {DISCOVERY_MAX_LANGUAGE_LENGTH} characters")
        try:
            detail = tmdb_client.get_movie_details(movie_id, language=lang)
            credits = tmdb_client.get_movie_credits(movie_id)
        except RuntimeError:
            raise HTTPException(status_code=503, detail="TMDb not configured")
        except TmdbClientError as e:
            logger.warning("Movie detail request failed: %s", e)
            raise HTTPException(status_code=502, detail="Movie details unavailable")
        except Exception:
            logger.exception("Movie detail request failed")
            raise HTTPException(status_code=502, detail="Movie details unavailable")
        cast_raw = credits.get("cast") or []
        cast = [
            CastMember(
                id=c.get("id", 0),
                name=c.get("name"),
                character=c.get("character"),
                profile_path=c.get("profile_path"),
            )
            for c in cast_raw[:20]
            if isinstance(c, dict) and c.get("id")
        ]
        genres = detail.get("genres") or []
        if not isinstance(genres, list):
            genres = []
        return MovieDetailResponse(
            id=detail.get("id", movie_id),
            title=detail.get("title"),
            poster_path=detail.get("poster_path"),
            release_date=detail.get("release_date"),
            vote_average=detail.get("vote_average"),
            overview=(detail.get("overview") or "")[:2000] or None,
            tagline=detail.get("tagline") or None,
            genres=[g for g in genres if isinstance(g, dict)],
            runtime=detail.get("runtime"),
            cast=cast,
        )

    @app.get("/people/{person_id}", response_model=PersonDetailResponse)
    async def get_person_detail(person_id: int, language: str = "en-US"):
        """Person detail page: full person info plus movie/TV credits."""
        if person_id < 1:
            raise HTTPException(status_code=400, detail="person_id must be a positive integer")
        lang = (language or "en-US").strip()
        if len(lang) > DISCOVERY_MAX_LANGUAGE_LENGTH:
            raise HTTPException(status_code=400, detail=f"language must be at most {DISCOVERY_MAX_LANGUAGE_LENGTH} characters")
        try:
            detail = tmdb_client.get_person_details(person_id, language=lang)
            movie_credits = tmdb_client.get_person_movie_credits(person_id)
            tv_credits = tmdb_client.get_person_tv_credits(person_id)
        except RuntimeError:
            raise HTTPException(status_code=503, detail="TMDb not configured")
        except TmdbClientError as e:
            logger.warning("Person detail request failed: %s", e)
            raise HTTPException(status_code=502, detail="Person details unavailable")
        except Exception:
            logger.exception("Person detail request failed")
            raise HTTPException(status_code=502, detail="Person details unavailable")
        known_for_raw = detail.get("known_for") or []
        known_for = []
        for k in known_for_raw:
            if isinstance(k, dict):
                known_for.append(k.get("title") or k.get("name") or "")
            elif isinstance(k, str):
                known_for.append(k)
        movie_cast = (movie_credits.get("cast") or [])[:15]
        tv_cast = (tv_credits.get("cast") or [])[:15]
        return PersonDetailResponse(
            id=detail.get("id", person_id),
            name=detail.get("name"),
            profile_path=detail.get("profile_path"),
            known_for_department=detail.get("known_for_department"),
            known_for=[t for t in known_for if t][:10],
            biography=(detail.get("biography") or "")[:2000] or None,
            birthday=detail.get("birthday"),
            place_of_birth=detail.get("place_of_birth"),
            movie_credits=[{"id": c.get("id"), "title": c.get("title"), "release_date": c.get("release_date"), "character": c.get("character")} for c in movie_cast if isinstance(c, dict) and c.get("id")],
            tv_credits=[{"id": c.get("id"), "name": c.get("name"), "first_air_date": c.get("first_air_date"), "character": c.get("character")} for c in tv_cast if isinstance(c, dict) and c.get("id")],
        )

    @app.get("/tv/{tv_id}", response_model=TvDetailResponse)
    async def get_tv_detail(tv_id: int, language: str = "en-US"):
        """TV show detail page: full show info plus cast."""
        if tv_id < 1:
            raise HTTPException(status_code=400, detail="tv_id must be a positive integer")
        lang = (language or "en-US").strip()
        if len(lang) > DISCOVERY_MAX_LANGUAGE_LENGTH:
            raise HTTPException(status_code=400, detail=f"language must be at most {DISCOVERY_MAX_LANGUAGE_LENGTH} characters")
        try:
            detail = tmdb_client.get_tv_details(tv_id, language=lang)
            credits = tmdb_client.get_tv_credits(tv_id)
        except RuntimeError:
            raise HTTPException(status_code=503, detail="TMDb not configured")
        except TmdbClientError as e:
            logger.warning("TV detail request failed: %s", e)
            raise HTTPException(status_code=502, detail="TV details unavailable")
        except Exception:
            logger.exception("TV detail request failed")
            raise HTTPException(status_code=502, detail="TV details unavailable")
        cast_raw = credits.get("cast") or []
        cast = [
            CastMember(id=c.get("id", 0), name=c.get("name"), character=c.get("character"), profile_path=c.get("profile_path"))
            for c in cast_raw[:20]
            if isinstance(c, dict) and c.get("id")
        ]
        genres = detail.get("genres") or []
        return TvDetailResponse(
            id=detail.get("id", tv_id),
            name=detail.get("name"),
            poster_path=detail.get("poster_path"),
            first_air_date=detail.get("first_air_date"),
            vote_average=detail.get("vote_average"),
            overview=(detail.get("overview") or "")[:2000] or None,
            tagline=detail.get("tagline") or None,
            genres=[g for g in genres if isinstance(g, dict)],
            number_of_seasons=detail.get("number_of_seasons"),
            cast=cast,
        )

    @app.post("/chat", response_model=ChatResponse)
    async def chat(body: ChatRequest, request: Request):
        logger.info("chat request body: %s", body)
        message = (body.message or "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="message is required")

        agent = getattr(request.app.state, "agent", None)
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not ready")

        # If user set a region filter, prepend instruction so the agent passes region to movie tools
        region_instruction = ""
        if body.region and (r := (body.region or "").strip()) and len(r) == 2:
            region_upper = r.upper()
            region_instruction = (
                f"[User filter: only show movies/content from region {region_upper}. "
                f"When calling discover_movie, get_movie_popular, or get_movie_now_playing, always pass region=\"{region_upper}\".] "
            )

        try:
            result = None
            # Exponential backoff for Anthropic 429: 2.5s, 6s, 12s (more tool calls = more round-trips = rate limit risk)
            backoff_seconds = (2.5, 6.0, 12.0)
            max_attempts = 1 + len(backoff_seconds)
            for attempt in range(max_attempts):
                try:
                    # Cap graph steps to reduce Anthropic API round-trips and avoid 429 (default 25 is too high for heavy tool use)
                    result = await agent.ainvoke(
                        {
                            "messages": [
                                HumanMessage(content=region_instruction + message),
                            ],
                        },
                        config={"recursion_limit": 8},
                    )
                    break
                except RateLimitError:
                    if attempt < len(backoff_seconds):
                        delay = backoff_seconds[attempt]
                        logger.warning(
                            "Anthropic rate limit (429), retry %s/%s after %.1fs",
                            attempt + 1,
                            max_attempts - 1,
                            delay,
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.warning("Anthropic rate limit (429) exceeded after all retries")
                        raise HTTPException(
                            status_code=429,
                            detail="Rate limit exceeded. Please wait a moment and try again.",
                        )
            messages = result.get("messages") or []
            all_cards = extract_cards_from_agent_result(messages)
            for m in reversed(messages):
                if hasattr(m, "content") and m.content:
                    text = _message_content_to_text(m.content)
                    if text:
                        # Prefer cards that are actually mentioned in the AI response (title-like context).
                        mentioned = _filter_cards_mentioned_in_response(all_cards, text)
                        # Only show cards that were mentioned; if none match, show no cards (avoid wrong cards like "Boxing" when AI meant Rocky, Creed, etc.)
                        cards = mentioned[:CHAT_CARDS_MAX] if mentioned else []
                        return ChatResponse(response=text, reply_found=True, cards=cards)
            cards = all_cards[:CHAT_CARDS_MAX]
            return ChatResponse(
                response="I couldn't generate a reply. Please try again.",
                reply_found=False,
                cards=cards,
            )
        except HTTPException:
            raise
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
