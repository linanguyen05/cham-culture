"""Community media storage backed by Supabase Storage.

Thin adapter over :class:`SupabaseGateway` keeping the ``upload_image`` /
``delete_image`` interface the community service expects.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from uuid import uuid4

from app.supabase_client import SupabaseGateway

_EXT_BY_TYPE = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
_VIDEO_EXT_BY_TYPE = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
    "video/x-msvideo": ".avi",
    "video/mpeg": ".mpeg",
}


class StorageService:
    def __init__(self, gateway: SupabaseGateway) -> None:
        self.gateway = gateway

    async def upload_image(self, data: bytes, content_type: str, original_name: str) -> str:
        ext = self._extension(content_type, original_name)
        path = f"posts/{uuid4().hex}{ext}"
        return await self.gateway.upload_object(path, data, content_type or "image/png")

    async def upload_video(self, data: bytes, content_type: str, original_name: str) -> str:
        ext = self._video_extension(content_type, original_name)
        path = f"videos/{uuid4().hex}{ext}"
        return await self.gateway.upload_object(path, data, content_type or "video/mp4")

    async def upload_comment_media(
        self, data: bytes, content_type: str, original_name: str, is_video: bool = False
    ) -> str:
        if is_video:
            ext = self._video_extension(content_type, original_name)
            ct = content_type or "video/mp4"
        else:
            ext = self._extension(content_type, original_name)
            ct = content_type or "image/png"
        path = f"comments/{uuid4().hex}{ext}"
        return await self.gateway.upload_object(path, data, ct)

    async def delete_image(self, url: str) -> None:
        await self.gateway.delete_object_by_url(url)

    @staticmethod
    def _extension(content_type: str, original_name: str) -> str:
        if content_type in _EXT_BY_TYPE:
            return _EXT_BY_TYPE[content_type]
        suffix = PurePosixPath(original_name).suffix.lower()
        return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".png"

    @staticmethod
    def _video_extension(content_type: str, original_name: str) -> str:
        if content_type in _VIDEO_EXT_BY_TYPE:
            return _VIDEO_EXT_BY_TYPE[content_type]
        suffix = PurePosixPath(original_name).suffix.lower()
        return suffix if suffix in {".mp4", ".webm", ".mov", ".avi"} else ".mp4"
