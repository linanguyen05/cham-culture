"""Serve the canonical frontend from the same origin as the API.

Mounting the frontend at ``/`` (html=True) means the SPA and API share one
origin, so relative ``fetch('/login')`` / ``fetch('/api/...')`` calls and cookie
sessions work without CORS. Uploaded media lives in Supabase Storage (absolute
URLs), so no local uploads mount is needed. Registered last so API routes win.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import Settings


def mount_static(app: FastAPI, settings: Settings) -> None:
    frontend_path = settings.frontend_path
    if frontend_path.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
