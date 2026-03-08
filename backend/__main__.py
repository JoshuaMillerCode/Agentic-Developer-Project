"""Run the backend server: python -m backend (dev). For production use a process manager and env config."""
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
