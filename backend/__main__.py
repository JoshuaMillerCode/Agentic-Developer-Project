"""Run the backend server.

Usage: python -m backend (from project root, with venv active).

Environment:
  HOST   — Bind address (default: 0.0.0.0).
  PORT   — Port (default: 8000).
  RELOAD — Set to "true" for auto-reload during development (default: true).
           For production, set RELOAD=false and use a process manager (e.g. gunicorn + uvicorn worker).

The FastAPI app is backend.app:app.
"""
import os

import uvicorn

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").strip().lower() in ("1", "true", "yes")
    # Production: set RELOAD=false and use a process manager (e.g. gunicorn + uvicorn worker)
    uvicorn.run(
        "backend.app:app",
        host=host,
        port=port,
        reload=reload,
    )
