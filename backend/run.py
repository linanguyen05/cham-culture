"""Development entry point.

Run from the ``backend/`` directory so the ``app`` package is importable:

    python run.py
"""

import uvicorn

from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    reload = settings.environment == "development"
    uvicorn.run(
        "app:create_app",
        host="127.0.0.1",
        port=8000,
        reload=reload,
        factory=True,
    )
