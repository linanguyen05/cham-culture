"""
Profile API for Chăm Culture Community.

This module intentionally reuses the existing authentication middleware and
PostgreSQL pool from the Community backend. It does not create a second auth
system or a second database connection.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from psycopg.rows import dict_row

from app.middleware.auth import CurrentUser, get_current_user


router = APIRouter(
    prefix="/api/community/profiles",
    tags=["Profiles"],
)


@router.get("/{user_id}")
async def get_profile(
    request: Request,
    user_id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Return a user's public profile and all of their posts page-by-page.

    The email address is intentionally returned only when the requested
    profile belongs to the authenticated user.
    """

    resources = request.app.state.resources
    offset = (page - 1) * limit
    is_current_user = str(current_user.id) == str(user_id)

    async with resources.db_pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT
                    id::text AS id,
                    username,
                    email,
                    avatar_url
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )
            user_row = await cur.fetchone()

            if user_row is None:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "NOT_FOUND",
                        "message": "Người dùng không tồn tại.",
                    },
                )

            # Fetch one extra row to calculate has_next without a second count.
            await cur.execute(
                """
                SELECT
                    p.id::text AS id,
                    p.created_at,
                    COALESCE(p.content, '') AS content,
                    COALESCE(p.category, 'Chung') AS category,
                    p.shared_post_id::text AS shared_post_id,
                    COALESCE(p.image_url, '') AS image_url,

                    u.id::text AS author_id,
                    u.username AS author_username,
                    u.avatar_url AS author_avatar_url,

                    COALESCE(lc.like_count, 0)::int AS like_count,
                    COALESCE(cc.comment_count, 0)::int AS comment_count,

                    EXISTS (
                        SELECT 1
                        FROM post_likes my_like
                        WHERE my_like.post_id = p.id
                          AND my_like.user_id = %s
                    ) AS liked_by_current_user

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

                WHERE p.user_id = %s
                ORDER BY p.created_at DESC, p.id DESC
                LIMIT %s
                OFFSET %s
                """,
                (current_user.id, user_id, limit + 1, offset),
            )
            post_rows = await cur.fetchall()

            has_next = len(post_rows) > limit
            post_rows = post_rows[:limit]

            shared_ids = [
                row["shared_post_id"]
                for row in post_rows
                if row["shared_post_id"]
            ]

            originals: dict[str, dict[str, Any]] = {}
            if shared_ids:
                await cur.execute(
                    """
                    SELECT
                        p.id::text AS id,
                        p.created_at,
                        COALESCE(p.content, '') AS content,
                        COALESCE(p.image_url, '') AS image_url,
                        p.user_id::text AS author_id,
                        u.username AS author_username,
                        u.avatar_url AS author_avatar_url
                    FROM posts p
                    JOIN users u ON u.id = p.user_id
                    WHERE p.id::text = ANY(%s)
                    """,
                    (shared_ids,),
                )
                original_rows = await cur.fetchall()

                for original in original_rows:
                    originals[original["id"]] = {
                        "id": original["id"],
                        "created_at": original["created_at"],
                        "content": original["content"],
                        "image_urls": _decode_image_urls(original["image_url"]),
                        "author": {
                            "id": original["author_id"],
                            "username": original["author_username"] or "Người dùng",
                            "avatar_url": original["author_avatar_url"],
                        },
                    }

            await cur.execute(
                """
                SELECT COUNT(*)::int
                FROM posts
                WHERE user_id = %s
                """,
                (user_id,),
            )
            post_count = int((await cur.fetchone())[0])

    items: list[dict[str, Any]] = []

    for row in post_rows:
        items.append(
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "content": row["content"],
                "image_urls": _decode_image_urls(row["image_url"]),
                "category": row["category"],
                "shared_post_id": row["shared_post_id"],
                "author": {
                    "id": row["author_id"],
                    "username": row["author_username"] or "Người dùng",
                    "avatar_url": row["author_avatar_url"],
                },
                "like_count": row["like_count"],
                "comment_count": row["comment_count"],
                "liked_by_current_user": bool(row["liked_by_current_user"]),
                "original_post": originals.get(row["shared_post_id"]),
            }
        )

    profile_user: dict[str, Any] = {
        "id": user_row["id"],
        "username": user_row["username"] or "Người dùng",
        "avatar_url": user_row["avatar_url"],
    }

    if is_current_user:
        profile_user["email"] = user_row["email"] or ""

    return {
        "user": profile_user,
        "is_current_user": is_current_user,
        "post_count": post_count,
        "items": items,
        "pagination": {
            "page": page,
            "limit": limit,
            "has_next": has_next,
        },
    }


def _decode_image_urls(value: str | None) -> list[str]:
    """Decode current JSON-string storage and legacy comma-separated URLs."""

    if not value:
        return []

    text = value.strip()
    if not text:
        return []

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [
                str(item).strip()
                for item in parsed
                if str(item).strip()
            ]
    except json.JSONDecodeError:
        pass

    return [item.strip() for item in text.split(",") if item.strip()]
