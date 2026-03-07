"""
Pytest configuration for mcp-server tests.
Loads .env from project root and ensures mcp-server is on sys.path.
"""
import os
import sys

# mcp-server directory (so "from tools import tmdb_tools" works)
_mcp_server = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _mcp_server not in sys.path:
    sys.path.insert(0, _mcp_server)

# Load .env from project root using python-dotenv for correct parsing
try:
    from dotenv import load_dotenv
    _root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    load_dotenv(os.path.join(_root, ".env"))
except ImportError:
    # Fallback: best-effort manual parse if dotenv not installed.
    # Does not strip inline comments (e.g. KEY=value # comment); use python-dotenv for full compatibility.
    _root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    _env_path = os.path.join(_root, ".env")
    if os.path.isfile(_env_path):
        with open(_env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k and v:
                        os.environ.setdefault(k, v)


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: tests that call the real TMDB API (need TMDB_API_KEY)")
