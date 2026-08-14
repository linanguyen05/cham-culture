"""SQLite data access for the community feature.

Ported from the original psycopg/Postgres repository: same method surface and
return shapes, rewritten with parameterised SQLite queries and explicit UUID
ids. Like-toggle and inserts run inside transactions.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from app.db import Database


class CommunityRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_posts(
        self,
        *,
        current_user_id: str,
        category: str | None,
        sort: str,
        page: int,
        limit: int,
    ) -> tuple[list[dict[str, Any]], bool]:
        offset = (page - 1) * limit
        order_sql = (
            "like_count DESC, p.created_at DESC, p.id DESC"
            if sort == "popular"
            else "p.created_at DESC, p.id DESC"
        )
        filters = "WHERE 1=1"
        params: list[Any] = [current_user_id]
        if category:
            filters += " AND p.category = ?"
            params.append(category)

        query = f"""
            SELECT
                p.id AS id,
                p.created_at AS created_at,
                COALESCE(p.content, '') AS content,
                COALESCE(p.category, 'Chung') AS category,
                p.shared_post_id AS shared_post_id,
                u.id AS author_id,
                u.username AS author_username,
                u.avatar_url AS author_avatar_url,
                (SELECT COUNT(*) FROM post_likes pl WHERE pl.post_id = p.id) AS like_count,
                (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) AS comment_count,
                EXISTS(
                    SELECT 1 FROM post_likes my_like
                    WHERE my_like.post_id = p.id AND my_like.user_id = ?
                ) AS liked_by_current_user,
                COALESCE(p.image_url, '') AS image_url
            FROM posts p
            JOIN users u ON u.id = p.user_id
            {filters}
            ORDER BY {order_sql}
            LIMIT ? OFFSET ?
        """
        params.extend([limit + 1, offset])

        async with self.db.connection() as conn:
            async with conn.execute(query, tuple(params)) as cur:
                raw_rows = await cur.fetchall()

            rows = [dict(r) for r in raw_rows]
            has_next = len(rows) > limit
            rows = rows[:limit]

            original_ids = [r["shared_post_id"] for r in rows if r["shared_post_id"]]
            original_map = await self._fetch_original_posts(conn, original_ids)

        for row in rows:
            row["image_urls"] = self._decode_image_urls(row.pop("image_url", ""))
            row["author"] = {
                "id": row.pop("author_id"),
                "username": row.pop("author_username") or "Người dùng",
                "avatar_url": row.pop("author_avatar_url"),
            }
            row["like_count"] = int(row["like_count"] or 0)
            row["comment_count"] = int(row["comment_count"] or 0)
            row["liked_by_current_user"] = bool(row["liked_by_current_user"])
            row["original_post"] = original_map.get(row["shared_post_id"])
        return rows, has_next

    async def _fetch_original_posts(self, conn, ids: list[str]) -> dict[str, dict[str, Any]]:
        if not ids:
            return {}
        placeholders = ",".join("?" for _ in ids)
        query = f"""
            SELECT
                p.id AS id,
                p.created_at AS created_at,
                COALESCE(p.content, '') AS content,
                p.user_id AS user_id,
                COALESCE(p.image_url, '') AS image_url,
                u.username AS username,
                u.avatar_url AS avatar_url
            FROM posts p
            JOIN users u ON u.id = p.user_id
            WHERE p.id IN ({placeholders})
        """
        async with conn.execute(query, tuple(ids)) as cur:
            rows = [dict(r) for r in await cur.fetchall()]
        return {
            row["id"]: {
                "id": row["id"],
                "created_at": row["created_at"],
                "content": row["content"],
                "image_urls": self._decode_image_urls(row["image_url"]),
                "author": {
                    "id": row["user_id"],
                    "username": row["username"] or "Người dùng",
                    "avatar_url": row["avatar_url"],
                },
            }
            for row in rows
        }

    async def post_exists(self, post_id: str) -> bool:
        row = await self.db.fetchone("SELECT 1 FROM posts WHERE id = ?", (post_id,))
        return row is not None

    async def get_post_for_share(self, post_id: str) -> dict[str, Any] | None:
        row = await self.db.fetchone(
            "SELECT id, category FROM posts WHERE id = ?", (post_id,)
        )
        return dict(row) if row else None

    async def create_post(
        self,
        *,
        user_id: str,
        content: str,
        category: str,
        image_urls: list[str],
        shared_post_id: str | None = None,
    ) -> str:
        image_url = (
            json.dumps(image_urls, ensure_ascii=False, separators=(",", ":"))
            if image_urls
            else ""
        )
        post_id = uuid4().hex
        async with self.db.connection() as conn:
            await conn.execute(
                """
                INSERT INTO posts (id, content, image_url, user_id, category, shared_post_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (post_id, content, image_url, user_id, category, shared_post_id),
            )
            await conn.commit()
        return post_id

    async def add_comment(self, *, user_id: str, post_id: str, content: str) -> dict[str, Any]:
        comment_id = uuid4().hex
        async with self.db.connection() as conn:
            await conn.execute(
                "INSERT INTO comments (id, content, user_id, post_id) VALUES (?, ?, ?, ?)",
                (comment_id, content, user_id, post_id),
            )
            await conn.commit()
            async with conn.execute(
                "SELECT id, created_at, content FROM comments WHERE id = ?", (comment_id,)
            ) as cur:
                row = await cur.fetchone()
        return dict(row)

    async def list_comments(self, post_id: str) -> list[dict[str, Any]]:
        rows = await self.db.fetchall(
            """
            SELECT
                c.id AS id,
                c.created_at AS created_at,
                c.content AS content,
                u.id AS user_id,
                u.username AS username,
                u.avatar_url AS avatar_url
            FROM comments c
            JOIN users u ON u.id = c.user_id
            WHERE c.post_id = ?
            ORDER BY c.created_at ASC, c.id ASC
            """,
            (post_id,),
        )
        return [
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "content": row["content"],
                "user": {
                    "id": row["user_id"],
                    "username": row["username"] or "Người dùng",
                    "avatar_url": row["avatar_url"],
                },
            }
            for row in rows
        ]

    async def toggle_like(self, *, post_id: str, user_id: str) -> tuple[bool, int]:
        async with self.db.connection() as conn:
            async with conn.execute("SELECT 1 FROM posts WHERE id = ?", (post_id,)) as cur:
                if await cur.fetchone() is None:
                    raise LookupError("POST_NOT_FOUND")

            async with conn.execute(
                "SELECT 1 FROM post_likes WHERE post_id = ? AND user_id = ?",
                (post_id, user_id),
            ) as cur:
                existing = await cur.fetchone()

            if existing:
                await conn.execute(
                    "DELETE FROM post_likes WHERE post_id = ? AND user_id = ?",
                    (post_id, user_id),
                )
                liked = False
            else:
                await conn.execute(
                    """
                    INSERT INTO post_likes (post_id, user_id) VALUES (?, ?)
                    ON CONFLICT(post_id, user_id) DO NOTHING
                    """,
                    (post_id, user_id),
                )
                liked = True

            await conn.commit()
            async with conn.execute(
                "SELECT COUNT(*) AS c FROM post_likes WHERE post_id = ?", (post_id,)
            ) as cur:
                count = int((await cur.fetchone())["c"])
        return liked, count

    async def topic_stats(self) -> list[dict[str, Any]]:
        rows = await self.db.fetchall(
            """
            SELECT category, COUNT(id) AS post_count
            FROM posts
            WHERE category IS NOT NULL AND category <> ''
            GROUP BY category
            ORDER BY post_count DESC, category ASC
            """
        )
        return [{"category": r["category"], "post_count": int(r["post_count"])} for r in rows]

    async def active_members(self) -> list[dict[str, Any]]:
        rows = await self.db.fetchall(
            """
            SELECT
                p.user_id AS user_id,
                u.username AS username,
                u.avatar_url AS avatar_url,
                COUNT(p.id) AS post_count
            FROM posts p
            JOIN users u ON u.id = p.user_id
            GROUP BY p.user_id, u.username, u.avatar_url
            ORDER BY post_count DESC, u.username ASC
            LIMIT 5
            """
        )
        return [
            {
                "user_id": r["user_id"],
                "username": r["username"] or "Người dùng",
                "avatar_url": r["avatar_url"],
                "post_count": int(r["post_count"]),
            }
            for r in rows
        ]

    @staticmethod
    def _decode_image_urls(value: str | None) -> list[str]:
        if not value:
            return []
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass
        return [item.strip() for item in text.split(",") if item.strip()]
