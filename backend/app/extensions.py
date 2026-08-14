"""Shared application resources bound to the FastAPI lifespan."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from app.config import Settings
from app.db import Database
from app.storage.service import LocalStorageService


class AppResources:
    """Holds the shared DB handle and storage service for the app lifespan."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.db = Database(settings.database_file)
        self.storage = LocalStorageService(settings)

    async def startup(self) -> None:
        await self.db.init()

    async def close(self) -> None:
        # SQLite connections are opened per operation; nothing global to close.
        return None


@asynccontextmanager
async def lifespan_context(settings: Settings) -> AsyncIterator[AppResources]:
    resources = AppResources(settings)
    await resources.startup()
    try:
        yield resources
    finally:
        await resources.close()
