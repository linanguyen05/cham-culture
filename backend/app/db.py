"""Async SQLite data access.

A thin wrapper over :mod:`aiosqlite` that mirrors the connection-per-operation
pattern of the original psycopg pool. Each ``connection()`` yields a fresh
connection with ``Row`` factory and foreign keys enabled, so repositories can
run isolated transactions without cross-request interleaving.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import aiosqlite

SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)

    async def init(self) -> None:
        """Create the parent directory and apply the schema (idempotent)."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.executescript(schema_sql)
            await conn.commit()

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[aiosqlite.Connection]:
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
        finally:
            await conn.close()

    async def fetchone(self, sql: str, params: tuple = ()) -> aiosqlite.Row | None:
        async with self.connection() as conn:
            async with conn.execute(sql, params) as cur:
                return await cur.fetchone()

    async def fetchall(self, sql: str, params: tuple = ()) -> list[aiosqlite.Row]:
        async with self.connection() as conn:
            async with conn.execute(sql, params) as cur:
                return list(await cur.fetchall())

    async def execute(self, sql: str, params: tuple = ()) -> None:
        async with self.connection() as conn:
            await conn.execute(sql, params)
            await conn.commit()
