"""Local authentication service.

Replaces the Supabase Auth adapter with self-contained password auth backed by
the SQLite ``users`` table. Passwords are hashed with PBKDF2-HMAC-SHA256
(stdlib only — no native build step required on Windows).
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any
from uuid import uuid4

from app.db import Database

_ALGO = "pbkdf2_sha256"
_ITERATIONS = 200_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = os.urandom(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return f"{_ALGO}${_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt_hex, hash_hex = stored.split("$")
        if algo != _ALGO:
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


def new_user_id() -> str:
    return uuid4().hex


class UserService:
    """CRUD helpers for the ``users`` table."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        row = await self.db.fetchone(
            "SELECT id, username, email, password_hash, avatar_url FROM users WHERE email = ?",
            (email.strip().lower(),),
        )
        return dict(row) if row else None

    async def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        row = await self.db.fetchone(
            "SELECT id, username, email, password_hash, avatar_url FROM users WHERE id = ?",
            (user_id,),
        )
        return dict(row) if row else None

    async def create(self, *, email: str, password: str, username: str | None = None) -> dict[str, Any]:
        user_id = new_user_id()
        await self.db.execute(
            """
            INSERT INTO users (id, username, email, password_hash, avatar_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, username, email.strip().lower(), hash_password(password), None),
        )
        created = await self.get_by_id(user_id)
        assert created is not None
        return created

    async def update_profile(
        self, *, user_id: str, username: str | None = None, avatar_url: str | None = None
    ) -> dict[str, Any] | None:
        sets: list[str] = []
        params: list[Any] = []
        if username is not None:
            sets.append("username = ?")
            params.append(username)
        if avatar_url is not None:
            sets.append("avatar_url = ?")
            params.append(avatar_url)
        if sets:
            params.append(user_id)
            await self.db.execute(
                f"UPDATE users SET {', '.join(sets)} WHERE id = ?", tuple(params)
            )
        return await self.get_by_id(user_id)
