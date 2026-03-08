"""
Tests for backend API routes: GET /health, POST /chat, GET /configuration, GET /discovery/*.
Uses test lifespan (no MCP/LLM keys required). Discovery and config tests patch tmdb_client.
"""
import pytest
from unittest.mock import patch


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
        assert "cards" in data
        assert data["cards"] == []

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


class TestConfiguration:
    """GET /configuration"""

    def test_configuration_returns_503_when_tmdb_key_missing(self, client_no_agent):
        with patch("backend.app.tmdb_client.get_configuration") as m:
            m.side_effect = RuntimeError("TMDB_API_KEY is not set.")
            response = client_no_agent.get("/configuration")
        assert response.status_code == 503
        assert response.json()["detail"] == "TMDb not configured"

    def test_configuration_returns_200_with_mocked_config(self, client_no_agent):
        with patch("backend.app.tmdb_client.get_configuration") as m:
            m.return_value = {"images": {"base_url": "https://image.tmdb.org/t/p/", "secure_base_url": "https://image.tmdb.org/t/p/"}}
            response = client_no_agent.get("/configuration")
        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert data["images"]["base_url"] == "https://image.tmdb.org/t/p/"


class TestDiscovery:
    """GET /discovery/*"""

    def test_discovery_movies_popular_returns_400_for_invalid_page(self, client_no_agent):
        with patch("backend.app.tmdb_client.get_movie_popular"):
            response = client_no_agent.get("/discovery/movies/popular?page=0")
        assert response.status_code == 400
        assert "page" in (response.json().get("detail") or "")

    def test_discovery_movies_popular_returns_200_with_mocked_data(self, client_no_agent):
        with patch("backend.app.tmdb_client.get_movie_popular") as m:
            m.return_value = {
                "page": 1,
                "total_pages": 1,
                "total_results": 1,
                "results": [{"id": 1, "title": "Test Movie", "poster_path": "/x", "release_date": "2024-01-01", "vote_average": 8.0, "overview": "A test"}],
            }
            response = client_no_agent.get("/discovery/movies/popular?page=1")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["page"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["type"] == "movie"
        assert data["results"][0]["title"] == "Test Movie"

    def test_discovery_people_trending_returns_400_for_invalid_time_window(self, client_no_agent):
        response = client_no_agent.get("/discovery/people/trending?time_window=month")
        assert response.status_code == 400
        assert "time_window" in (response.json().get("detail") or "")
