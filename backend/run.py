"""Development entry point.

Run from the ``backend/`` directory so the ``app`` package is importable:

    python run.py

On Windows we force the Selector event loop because psycopg's async mode does
not support the default Proactor loop.
"""

import asyncio
import sys

import uvicorn

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    uvicorn.run(
        "app:create_app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        factory=True,
        loop="asyncio",
    )
