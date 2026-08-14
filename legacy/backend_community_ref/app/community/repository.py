import json
from typing import Any

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool


class CommunityRepository:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self.pool = pool

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
        filters = "WHERE TRUE"
        params: list[Any] = [current_user_id]
        if category:
            filters += " AND p.category = %s"
            params.append(category)

        query = f"""
            SELECT
                p.id::text AS id,
                p.created_at,
                COALESCE(p.content, '') AS content,
                COALESCE(p.category, 'Chung') AS category,
                p.shared_post_id::text AS shared_post_id,
                u.id::text AS author_id,
                u.username AS author_username,
                u.avatar_url AS author_avatar_url,
                COALESCE(lc.like_count, 0)::int AS like_count,
                COALESCE(cc.comment_count, 0)::int AS comment_count,
                EXISTS(
                    SELECT 1 FROM post_likes my_like
                    WHERE my_like.post_id = p.id
                      AND my_like.user_id = %s
                ) AS liked_by_current_user,
                COALESCE(p.image_url, '') AS image_url
            FROM posts p
            JOIN users u ON u.id = p.user_id
            LEFT JOIN (
                SELECT post_id, COUNT(*)::int AS like_count
                FROM post_likes
                GROUP BY post_id
            ) lc ON lc.post_id = p.id
            LEFT JOIN (
                SELECT post_id, COUNT(*)::int AS comment_count
                FROM comments
                GROUP BY post_id
            ) cc ON cc.post_id = p.id
            {filters}
            ORDER BY {order_sql}
            LIMIT %s OFFSET %s
        """
        params.extend([limit + 1, offset])

        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params)
                rows = await cur.fetchall()

                has_next = len(rows) > limit
                rows = rows[:limit]

                original_ids = [row["shared_post_id"] for row in rows if row["shared_post_id"]]
                original_map = await self._fetch_original_posts(conn, original_ids)

        for row in rows:
            row["image_urls"] = self._decode_image_urls(row.pop("image_url", ""))
            row["author"] = {
                "id": row.pop("author_id"),
                "username": row.pop("author_username") or "Người dùng",
                "avatar_url": row.pop("author_avatar_url"),
            }
            row["original_post"] = original_map.get(row["shared_post_id"])
        return rows, has_next

    async def _fetch_original_posts(self, conn, ids: list[str]) -> dict[str, dict[str, Any]]:
        if not ids:
            return {}
        query = """
            SELECT
                p.id::text AS id,
                p.created_at,
                COALESCE(p.content, '') AS content,
                p.user_id::text AS user_id,
                COALESCE(p.image_url, '') AS image_url,
                u.username,
                u.avatar_url
            FROM posts p
            JOIN users u ON u.id = p.user_id
            WHERE p.id::text = ANY(%s)
        """
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, (ids,))
            rows = await cur.fetchall()
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
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1 FROM posts WHERE id = %s", (post_id,))
                return (await cur.fetchone()) is not None

    async def get_post_for_share(self, post_id: str) -> dict[str, Any] | None:
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT id::text AS id, category
                    FROM posts
                    WHERE id = %s
                    """,
                    (post_id,),
                )
                return await cur.fetchone()

    async def create_post(
        self,
        *,
        user_id: str,
        content: str,
        category: str,
        image_urls: list[str],
        shared_post_id: str | None = None,
    ) -> str:
        image_url = json.dumps(image_urls, ensure_ascii=False, separators=(",", ":")) if image_urls else ""
        async with self.pool.connection() as conn:
            async with conn.transaction():
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        INSERT INTO posts (content, image_url, user_id, category, shared_post_id)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id::text
                        """,
                        (content, image_url, user_id, category, shared_post_id),
                    )
                    row = await cur.fetchone()
                    if row is None:
                        raise RuntimeError("Insert post did not return id")
                    return row[0]

    async def add_comment(self, *, user_id: str, post_id: str, content: str) -> dict[str, Any]:
        async with self.pool.connection() as conn:
            async with conn.transaction():
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(
                        """
                        INSERT INTO comments (content, user_id, post_id)
                        VALUES (%s, %s, %s)
                        RETURNING id::text AS id, created_at, content
                        """,
                        (content, user_id, post_id),
                    )
                    row = await cur.fetchone()
                    if row is None:
                        raise RuntimeError("Insert comment did not return row")
                    return row

    async def list_comments(self, post_id: str) -> list[dict[str, Any]]:
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT
                        c.id::text AS id,
                        c.created_at,
                        c.content,
                        u.id::text AS user_id,
                        u.username,
                        u.avatar_url
                    FROM comments c
                    JOIN users u ON u.id = c.user_id
                    WHERE c.post_id = %s
                    ORDER BY c.created_at ASC, c.id ASC
                    """,
                    (post_id,),
                )
                rows = await cur.fetchall()
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
        async with self.pool.connection() as conn:
            async with conn.transaction():
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1 FROM posts WHERE id = %s", (post_id,))
                    if await cur.fetchone() is None:
                        raise LookupError("POST_NOT_FOUND")

                    await cur.execute(
                        """
                        SELECT 1 FROM post_likes
                        WHERE post_id = %s AND user_id = %s
                        FOR UPDATE
                        """,
                        (post_id, user_id),
                    )
                    existing = await cur.fetchone()
                    if existing:
                        await cur.execute(
                            "DELETE FROM post_likes WHERE post_id = %s AND user_id = %s",
                            (post_id, user_id),
                        )
                        liked = False
                    else:
                        # Composite PK prevents duplicates even under concurrent requests.
                        await cur.execute(
                            """
                            INSERT INTO post_likes (post_id, user_id)
                            VALUES (%s, %s)
                            ON CONFLICT (post_id, user_id) DO NOTHING
                            """,
                            (post_id, user_id),
                        )
                        liked = True

                    await cur.execute(
                        "SELECT COUNT(*)::int FROM post_likes WHERE post_id = %s",
                        (post_id,),
                    )
                    count = (await cur.fetchone())[0]
                    return liked, count

    async def topic_stats(self) -> list[dict[str, Any]]:
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT category, COUNT(id)::int AS post_count
                    FROM posts
                    WHERE category IS NOT NULL AND category <> ''
                    GROUP BY category
                    ORDER BY post_count DESC, category ASC
                    """
                )
                return list(await cur.fetchall())

    async def active_members(self) -> list[dict[str, Any]]:
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT
                        p.user_id::text AS user_id,
                        u.username,
                        u.avatar_url,
                        COUNT(p.id)::int AS post_count
                    FROM posts p
                    JOIN users u ON u.id = p.user_id
                    GROUP BY p.user_id, u.username, u.avatar_url
                    ORDER BY post_count DESC, u.username ASC
                    LIMIT 5
                    """
                )
                return list(await cur.fetchall())

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
