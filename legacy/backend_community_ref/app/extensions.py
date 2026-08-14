from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from psycopg_pool import AsyncConnectionPool
from supabase import Client, create_client

from app.config import Settings


class AppResources:
    """Holds shared clients/pools for the application lifespan."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.db_pool = AsyncConnectionPool(
            conninfo=settings.database_url,
            min_size=settings.database_min_size,
            max_size=settings.database_max_size,
            open=False,
        )
        self.supabase_storage: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
        self.http_client = httpx.AsyncClient(timeout=httpx.Timeout(15.0))

    async def close(self) -> None:
        await self.http_client.aclose()
        await self.db_pool.close()


@asynccontextmanager
async def lifespan_context(settings: Settings) -> AsyncIterator[AppResources]:
    resources = AppResources(settings)
    await resources.db_pool.open(wait=True)
    try:
        yield resources
    finally:
        await resources.close()
