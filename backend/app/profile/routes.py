"""Profile API — a user's public profile plus their posts, paginated.

Reuses the shared session auth and the same SQLite database as Community. The
email field is returned only when the requested profile is the caller's own.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.community.repository import CommunityRepository
from app.middleware.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/api/community/profiles", tags=["Profiles"])


@router.get("/{user_id}")
async def get_profile(
    request: Request,
    user_id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    db = request.app.state.resources.db
    offset = (page - 1) * limit
    is_current_user = str(current_user.id) == str(user_id)

    user_row = await db.fetchone(
        "SELECT id, username, email, avatar_url FROM users WHERE id = ?",
        (user_id,),
    )
    if user_row is None:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Người dùng không tồn tại."})

    post_rows = [
        dict(r)
        for r in await db.fetchall(
            """
            SELECT
                p.id AS id,
                p.created_at AS created_at,
                COALESCE(p.content, '') AS content,
                COALESCE(p.category, 'Chung') AS category,
                p.shared_post_id AS shared_post_id,
                COALESCE(p.image_url, '') AS image_url,
                u.id AS author_id,
                u.username AS author_username,
                u.avatar_url AS author_avatar_url,
                (SELECT COUNT(*) FROM post_likes pl WHERE pl.post_id = p.id) AS like_count,
                (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) AS comment_count,
                EXISTS(
                    SELECT 1 FROM post_likes my_like
                    WHERE my_like.post_id = p.id AND my_like.user_id = ?
                ) AS liked_by_current_user
            FROM posts p
            JOIN users u ON u.id = p.user_id
            WHERE p.user_id = ?
            ORDER BY p.created_at DESC, p.id DESC
            LIMIT ? OFFSET ?
            """,
            (current_user.id, user_id, limit + 1, offset),
        )
    ]

    has_next = len(post_rows) > limit
    post_rows = post_rows[:limit]

    shared_ids = [r["shared_post_id"] for r in post_rows if r["shared_post_id"]]
    originals: dict[str, dict[str, Any]] = {}
    if shared_ids:
        placeholders = ",".join("?" for _ in shared_ids)
        original_rows = await db.fetchall(
            f"""
            SELECT
                p.id AS id,
                p.created_at AS created_at,
                COALESCE(p.content, '') AS content,
                COALESCE(p.image_url, '') AS image_url,
                p.user_id AS author_id,
                u.username AS author_username,
                u.avatar_url AS author_avatar_url
            FROM posts p
            JOIN users u ON u.id = p.user_id
            WHERE p.id IN ({placeholders})
            """,
            tuple(shared_ids),
        )
        for original in (dict(r) for r in original_rows):
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

    count_row = await db.fetchone(
        "SELECT COUNT(*) AS c FROM posts WHERE user_id = ?", (user_id,)
    )
    post_count = int(count_row["c"])

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
                "like_count": int(row["like_count"] or 0),
                "comment_count": int(row["comment_count"] or 0),
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
        "pagination": {"page": page, "limit": limit, "has_next": has_next},
    }


def _decode_image_urls(value: str | None) -> list[str]:
    return CommunityRepository._decode_image_urls(value)
