"""Shared application resources bound to the FastAPI lifespan.

Holds the psycopg async connection pool (Supabase PostgreSQL) and the Supabase
gateway (Auth + Storage over HTTPS).
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.config import Settings
from app.supabase_client import SupabaseGateway


class AppResources:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.pool = AsyncConnectionPool(
            conninfo=settings.db_conninfo,
            min_size=settings.database_min_size,
            max_size=settings.database_max_size,
            open=False,
            kwargs={"row_factory": dict_row},
        )
        self.http = httpx.AsyncClient()
        self.supa = SupabaseGateway(settings, self.http)

    async def startup(self) -> None:
        await self.pool.open(wait=True, timeout=30)
        try:
            await self.supa.ensure_bucket()
        except Exception:
            # Non-fatal: storage may be provisioned later; log-and-continue.
            import logging

            logging.getLogger(__name__).warning("Could not ensure storage bucket", exc_info=True)

    async def close(self) -> None:
        await self.pool.close()
        await self.http.aclose()


@asynccontextmanager
async def lifespan_context(settings: Settings) -> AsyncIterator[AppResources]:
    resources = AppResources(settings)
    await resources.startup()
    try:
        yield resources
    finally:
        await resources.close()
