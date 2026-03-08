"""
Tests for backend API routes: GET /health, POST /chat.
Uses test lifespan (no MCP/LLM keys required).
"""
import pytest


class TestHealth:
    """GET /health"""

    def test_health_returns_503_when_agent_not_ready(self, client_no_agent):
        response = client_no_agent.get("/health")
        assert response.status_code == 503
        assert response.json() == {"detail": "Agent not ready"}

    def test_health_returns_200_when_agent_ready(self, client_with_agent):
        response = client_with_agent.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestChat:
    """POST /chat"""

    def test_chat_returns_422_when_body_empty(self, client_with_agent):
        response = client_with_agent.post("/chat", json={})
        assert response.status_code == 422

    def test_chat_returns_422_when_message_missing(self, client_with_agent):
        response = client_with_agent.post("/chat", json={"other": "field"})
        assert response.status_code == 422

    def test_chat_returns_400_when_message_empty_string(self, client_with_agent):
        response = client_with_agent.post("/chat", json={"message": ""})
        # Pydantic min_length=1 may give 422; route also checks strip and returns 400
        assert response.status_code in (400, 422)
        data = response.json()
        assert "detail" in data

    def test_chat_returns_400_when_message_whitespace_only(self, client_with_agent):
        response = client_with_agent.post("/chat", json={"message": "   "})
        assert response.status_code in (400, 422)

    def test_chat_returns_503_when_agent_not_ready(self, client_no_agent):
        response = client_no_agent.post("/chat", json={"message": "Hello"})
        assert response.status_code == 503
        assert response.json() == {"detail": "Agent not ready"}

    def test_chat_returns_200_with_mock_reply(self, client_with_agent):
        response = client_with_agent.post("/chat", json={"message": "Hi"})
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["response"] == "Mock reply for testing."
        assert data["reply_found"] is True

    def test_chat_returns_200_with_reply_found_false_when_no_final_text(
        self, client_agent_no_reply
    ):
        response = client_agent_no_reply.post("/chat", json={"message": "Hi"})
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "I couldn't generate a reply. Please try again."
        assert data["reply_found"] is False

    def test_chat_rejects_message_over_max_length(self, client_with_agent):
        response = client_with_agent.post(
            "/chat",
            json={"message": "x" * 32_001},
        )
        assert response.status_code == 422
