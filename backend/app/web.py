"""Serve the canonical frontend and uploaded media from the same origin.

Mounting the frontend at ``/`` (with ``html=True``) means the SPA and the API
share one origin, so the frontend's relative ``fetch('/login')`` /
``fetch('/api/...')`` calls and cookie sessions work without CORS. Mounts are
registered last so all API routes take precedence.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import Settings


def mount_static(app: FastAPI, settings: Settings) -> None:
    upload_path = settings.upload_path
    upload_path.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

    frontend_path = settings.frontend_path
    if frontend_path.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
