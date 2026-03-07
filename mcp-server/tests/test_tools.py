"""
Tests for all TMDB MCP tools.
- Validation tests: no API key needed; assert validation_error responses.
- Integration tests: require TMDB_API_KEY in env; call real API and assert structure.
"""
import json
import os

import pytest

from tools import tmdb_tools

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _has_api_key():
    key = os.environ.get("TMDB_API_KEY") or ""
    return bool(key.strip())


def _parse(raw: str) -> dict:
    return json.loads(raw)


def _is_success(data: dict) -> bool:
    return "error" not in data


# ---------------------------------------------------------------------------
# Validation tests (no API key required)
# ---------------------------------------------------------------------------


class TestSearchMovieValidation:
    def test_empty_query_returns_validation_error(self):
        raw = tmdb_tools.search_movie("")
        data = _parse(raw)
        assert data.get("error") == "validation_error"
        assert "non-empty" in data.get("detail", "").lower()

    def test_query_too_long_returns_validation_error(self):
        raw = tmdb_tools.search_movie("x" * 501)
        data = _parse(raw)
        assert data.get("error") == "validation_error"
        assert "500" in data.get("detail", "") or "character" in data.get("detail", "").lower()

    def test_invalid_page_type_returns_validation_error(self):
        raw = tmdb_tools.search_movie("Matrix", page="not_a_number")
        data = _parse(raw)
        assert data.get("error") == "validation_error"
        assert "integer" in data.get("detail", "").lower()

    def test_page_zero_returns_validation_error(self):
        raw = tmdb_tools.search_movie("Matrix", page=0)
        data = _parse(raw)
        assert data.get("error") == "validation_error"


class TestSearchTvValidation:
    def test_empty_query_returns_validation_error(self):
        raw = tmdb_tools.search_tv("")
        data = _parse(raw)
        assert data.get("error") == "validation_error"

    def test_invalid_page_returns_validation_error(self):
        raw = tmdb_tools.search_tv("Breaking Bad", page=99999)
        data = _parse(raw)
        assert data.get("error") == "validation_error"
        assert "page" in data.get("detail", "").lower() or "500" in data.get("detail", "")

    def test_query_too_long_returns_validation_error(self):
        raw = tmdb_tools.search_tv("x" * 501)
        data = _parse(raw)
        assert data.get("error") == "validation_error"
        assert "500" in data.get("detail", "") or "character" in data.get("detail", "").lower()


class TestDiscoverMovieValidation:
    def test_invalid_sort_by_returns_validation_error(self):
        raw = tmdb_tools.discover_movie(sort_by="invalid.sort")
        data = _parse(raw)
        assert data.get("error") == "validation_error"
        assert "sort_by" in data.get("detail", "").lower()

    def test_invalid_year_returns_validation_error(self):
        raw = tmdb_tools.discover_movie(year=1800)
        data = _parse(raw)
        assert data.get("error") == "validation_error"
        assert "1900" in data.get("detail", "")

    def test_invalid_vote_average_returns_validation_error(self):
        raw = tmdb_tools.discover_movie(vote_average_gte=11)
        data = _parse(raw)
        assert data.get("error") == "validation_error"
        assert "10" in data.get("detail", "") or "vote" in data.get("detail", "").lower()

    def test_vote_average_gte_greater_than_lte_returns_validation_error(self):
        raw = tmdb_tools.discover_movie(vote_average_gte=8, vote_average_lte=5)
        data = _parse(raw)
        assert data.get("error") == "validation_error"
        assert "vote" in data.get("detail", "").lower()

    def test_invalid_with_genres_returns_validation_error(self):
        raw = tmdb_tools.discover_movie(with_genres="action,not_a_number")
        data = _parse(raw)
        assert data.get("error") == "validation_error"
        assert "genre" in data.get("detail", "").lower() or "digit" in data.get("detail", "").lower()


class TestGetMovieDetailsValidation:
    def test_negative_id_returns_validation_error(self):
        raw = tmdb_tools.get_movie_details(-1)
        data = _parse(raw)
        assert data.get("error") == "validation_error"

    def test_invalid_id_type_returns_validation_error(self):
        raw = tmdb_tools.get_movie_details("not_an_id")
        data = _parse(raw)
        assert data.get("error") == "validation_error"


class TestGetTvDetailsValidation:
    def test_zero_id_returns_validation_error(self):
        raw = tmdb_tools.get_tv_details(0)
        data = _parse(raw)
        assert data.get("error") == "validation_error"

    def test_negative_id_returns_validation_error(self):
        raw = tmdb_tools.get_tv_details(-1)
        data = _parse(raw)
        assert data.get("error") == "validation_error"

    def test_invalid_id_type_returns_validation_error(self):
        raw = tmdb_tools.get_tv_details("not_an_id")
        data = _parse(raw)
        assert data.get("error") == "validation_error"


class TestTrendingValidation:
    def test_invalid_time_window_movies_returns_validation_error(self):
        raw = tmdb_tools.get_trending_movies("month")
        data = _parse(raw)
        assert data.get("error") == "validation_error"
        assert "day" in data.get("detail", "").lower() or "week" in data.get("detail", "").lower()

    def test_invalid_time_window_tv_returns_validation_error(self):
        raw = tmdb_tools.get_trending_tv("year")
        data = _parse(raw)
        assert data.get("error") == "validation_error"
        assert "day" in data.get("detail", "").lower() or "week" in data.get("detail", "").lower()


# ---------------------------------------------------------------------------
# Error response shape (no API key needed for request_failed path)
# ---------------------------------------------------------------------------


class TestErrorResponseShape:
    """Ensure error paths return safe JSON only (no stack traces or exception text)."""

    def test_missing_api_key_returns_safe_error(self):
        env_val = os.environ.pop("TMDB_API_KEY", None)
        try:
            raw = tmdb_tools.get_configuration()
            data = _parse(raw)
            assert data.get("error") in ("request_failed", "api_error")
            assert "detail" in data or "status_code" in data
            assert "Traceback" not in raw
            assert "RuntimeError" not in raw
            assert "TMDB_API_KEY" not in raw
        finally:
            if env_val is not None:
                os.environ["TMDB_API_KEY"] = env_val

    def test_validation_error_has_expected_shape(self):
        raw = tmdb_tools.search_movie("")
        data = _parse(raw)
        assert data.get("error") == "validation_error"
        assert "detail" in data
        assert isinstance(data["detail"], str)


# ---------------------------------------------------------------------------
# Integration tests (require TMDB_API_KEY)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.skipif(not _has_api_key(), reason="TMDB_API_KEY not set")
class TestGetConfigurationIntegration:
    def test_returns_images_and_languages(self):
        raw = tmdb_tools.get_configuration()
        data = _parse(raw)
        assert _is_success(data)
        assert "images" in data
        assert "base_url" in data["images"] or "secure_base_url" in data["images"]


@pytest.mark.integration
@pytest.mark.skipif(not _has_api_key(), reason="TMDB_API_KEY not set")
class TestSearchMovieIntegration:
    def test_returns_results_structure(self):
        raw = tmdb_tools.search_movie("Matrix", 1)
        data = _parse(raw)
        assert _is_success(data)
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_accepts_string_page(self):
        raw = tmdb_tools.search_movie("Inception", page="1")
        data = _parse(raw)
        assert _is_success(data)
        assert "results" in data


@pytest.mark.integration
@pytest.mark.skipif(not _has_api_key(), reason="TMDB_API_KEY not set")
class TestSearchTvIntegration:
    def test_returns_results_structure(self):
        raw = tmdb_tools.search_tv("Breaking Bad", 1)
        data = _parse(raw)
        assert _is_success(data)
        assert "results" in data


@pytest.mark.integration
@pytest.mark.skipif(not _has_api_key(), reason="TMDB_API_KEY not set")
class TestDiscoverMovieIntegration:
    def test_returns_results_structure(self):
        raw = tmdb_tools.discover_movie("popularity.desc", 1)
        data = _parse(raw)
        assert _is_success(data)
        assert "results" in data

    def test_accepts_normalized_sort_by(self):
        raw = tmdb_tools.discover_movie(sort_by="  POPULARITY.DESC  ")
        data = _parse(raw)
        assert _is_success(data)


@pytest.mark.integration
@pytest.mark.skipif(not _has_api_key(), reason="TMDB_API_KEY not set")
class TestGetMovieDetailsIntegration:
    """Integration tests use TMDB IDs 603 (movie) and 1396 (TV). Response structure is asserted; exact titles may vary if TMDB data changes."""

    def test_returns_movie_with_title(self):
        raw = tmdb_tools.get_movie_details(603)  # The Matrix
        data = _parse(raw)
        assert _is_success(data)
        assert "title" in data
        assert isinstance(data["title"], str)

    def test_accepts_string_id(self):
        raw = tmdb_tools.get_movie_details("603")
        data = _parse(raw)
        assert _is_success(data)
        assert "title" in data
        assert isinstance(data.get("title"), str)


@pytest.mark.integration
@pytest.mark.skipif(not _has_api_key(), reason="TMDB_API_KEY not set")
class TestGetTvDetailsIntegration:
    def test_returns_show_with_name(self):
        raw = tmdb_tools.get_tv_details(1396)  # Breaking Bad
        data = _parse(raw)
        assert _is_success(data)
        assert "name" in data
        assert isinstance(data["name"], str)


@pytest.mark.integration
@pytest.mark.skipif(not _has_api_key(), reason="TMDB_API_KEY not set")
class TestGetTrendingMoviesIntegration:
    def test_day_returns_results(self):
        raw = tmdb_tools.get_trending_movies("day")
        data = _parse(raw)
        assert _is_success(data)
        assert "results" in data

    def test_week_returns_results(self):
        raw = tmdb_tools.get_trending_movies("week")
        data = _parse(raw)
        assert _is_success(data)


@pytest.mark.integration
@pytest.mark.skipif(not _has_api_key(), reason="TMDB_API_KEY not set")
class TestGetTrendingTvIntegration:
    def test_day_returns_results(self):
        raw = tmdb_tools.get_trending_tv("day")
        data = _parse(raw)
        assert _is_success(data)

    def test_week_returns_results(self):
        raw = tmdb_tools.get_trending_tv("week")
        data = _parse(raw)
        assert _is_success(data)
