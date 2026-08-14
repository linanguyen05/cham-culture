from pathlib import PurePosixPath
from uuid import uuid4

from supabase import Client

from app.config import Settings


class StorageService:
    """Uploads community media to Supabase Storage using a server-only client."""

    def __init__(self, client: Client, settings: Settings) -> None:
        self.client = client
        self.settings = settings

    async def upload_image(self, data: bytes, content_type: str, original_name: str) -> str:
        ext = self._extension(content_type, original_name)
        path = str(PurePosixPath("posts") / f"{uuid4().hex}{ext}")
        options = {"content-type": content_type, "upsert": False}

        # Supabase client methods are synchronous; execute them off the event loop.
        import asyncio

        def do_upload() -> None:
            self.client.storage.from_(self.settings.supabase_storage_bucket).upload(
                path, data, options
            )

        await asyncio.to_thread(do_upload)
        if self.settings.supabase_storage_public:
            return (
                f"{self.settings.supabase_url.rstrip('/')}/storage/v1/object/public/"
                f"{self.settings.supabase_storage_bucket}/{path}"
            )
        signed = await asyncio.to_thread(
            self.client.storage.from_(self.settings.supabase_storage_bucket).create_signed_url,
            path,
            60 * 60 * 24,
        )
        return signed["signedURL"]

    async def delete_image(self, public_or_signed_url: str) -> None:
        prefix = (
            f"{self.settings.supabase_url.rstrip('/')}/storage/v1/object/public/"
            f"{self.settings.supabase_storage_bucket}/"
        )
        if public_or_signed_url.startswith(prefix):
            path = public_or_signed_url[len(prefix):]
        else:
            marker = f"/storage/v1/object/{self.settings.supabase_storage_bucket}/"
            if marker not in public_or_signed_url:
                return
            path = public_or_signed_url.split(marker, 1)[1].split("?", 1)[0]

        import asyncio

        await asyncio.to_thread(
            self.client.storage.from_(self.settings.supabase_storage_bucket).remove,
            [path],
        )

    @staticmethod
    def _extension(content_type: str, original_name: str) -> str:
        mapping = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }
        if content_type in mapping:
            return mapping[content_type]
        suffix = PurePosixPath(original_name).suffix.lower()
        return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".bin"
