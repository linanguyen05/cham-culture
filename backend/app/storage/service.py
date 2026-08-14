"""Local filesystem media storage.

Drop-in replacement for the original Supabase Storage service. Files are written
under ``settings.upload_path`` and exposed through the ``/uploads`` static mount,
so the API keeps returning plain URLs the frontend can put in ``<img src>``.
"""

from __future__ import annotations

import asyncio
from pathlib import Path, PurePosixPath
from uuid import uuid4

from app.config import Settings

PUBLIC_PREFIX = "/uploads"

_EXT_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class LocalStorageService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_dir: Path = settings.upload_path

    async def upload_image(self, data: bytes, content_type: str, original_name: str) -> str:
        ext = self._extension(content_type, original_name)
        rel = PurePosixPath("community") / f"{uuid4().hex}{ext}"
        await self._write(rel, data)
        return f"{PUBLIC_PREFIX}/{rel}"

    async def save_avatar(self, data: bytes, content_type: str, original_name: str) -> str:
        ext = self._extension(content_type, original_name)
        rel = PurePosixPath("avatars") / f"{uuid4().hex}{ext}"
        await self._write(rel, data)
        return f"{PUBLIC_PREFIX}/{rel}"

    async def delete_image(self, url: str) -> None:
        prefix = f"{PUBLIC_PREFIX}/"
        if not url.startswith(prefix):
            return
        rel = url[len(prefix):]
        target = (self.base_dir / rel).resolve()
        # Guard against path traversal outside the upload directory.
        if self.base_dir.resolve() not in target.parents:
            return

        def _remove() -> None:
            try:
                target.unlink()
            except FileNotFoundError:
                pass

        await asyncio.to_thread(_remove)

    async def _write(self, rel: PurePosixPath, data: bytes) -> None:
        target = self.base_dir / rel

        def _do() -> None:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)

        await asyncio.to_thread(_do)

    @staticmethod
    def _extension(content_type: str, original_name: str) -> str:
        if content_type in _EXT_BY_TYPE:
            return _EXT_BY_TYPE[content_type]
        suffix = PurePosixPath(original_name).suffix.lower()
        return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"} else ".bin"
