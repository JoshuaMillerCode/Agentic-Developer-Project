"""
Pytest fixtures for backend route tests.
Uses a test lifespan so no MCP/LLM keys are required.
"""
from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from backend.app import create_app


@asynccontextmanager
async def _lifespan_no_agent(app):
    """Lifespan that does not set an agent (for 503 tests)."""
    yield


@asynccontextmanager
async def _lifespan_with_mock_agent(app):
    """Lifespan that sets a mock agent returning a fixed reply."""
    class MockAgent:
        async def ainvoke(self, _input):
            return {
                "messages": [
                    AIMessage(content="Mock reply for testing."),
                ],
            }

    app.state.agent = MockAgent()
    yield


@asynccontextmanager
async def _lifespan_with_mock_agent_no_reply(app):
    """Lifespan that sets a mock agent returning no final text (reply_found=False)."""
    class MockAgent:
        async def ainvoke(self, _input):
            return {"messages": []}

    app.state.agent = MockAgent()
    yield


@pytest.fixture
def client_no_agent():
    """Client with no agent (health 503, chat 503)."""
    app = create_app(lifespan_fn=_lifespan_no_agent)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_with_agent():
    """Client with mock agent (health 200, chat 200 with mock reply)."""
    app = create_app(lifespan_fn=_lifespan_with_mock_agent)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_agent_no_reply():
    """Client with mock agent that returns no final text (reply_found=False)."""
    app = create_app(lifespan_fn=_lifespan_with_mock_agent_no_reply)
    with TestClient(app) as c:
        yield c
