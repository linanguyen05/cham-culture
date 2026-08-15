"""Seed demo users (Supabase Auth) and posts (Supabase PostgreSQL).

Idempotent: existing users are reused; posts are only created when the posts
table is empty.

    python seed.py
"""

import asyncio
import sys

from app.auth.service import UserRepository
from app.community.repository import CommunityRepository
from app.config import get_settings
from app.extensions import lifespan_context
from app.supabase_client import AuthConflictError, SupabaseError

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

DEMO_USERS = [
    {"email": "minhanh@gmail.com", "username": "Minh Anh", "password": "123Aa2026", "avatar": "https://i.pravatar.cc/150?img=47"},
    {"email": "quangkhai@cham.vn", "username": "Quang Khải", "password": "chamculture", "avatar": "https://i.pravatar.cc/150?img=12"},
    {"email": "myduyen@cham.vn", "username": "Mỹ Duyên", "password": "chamculture", "avatar": "https://i.pravatar.cc/150?img=32"},
]

DEMO_POSTS = [
    ("Tháp Po Klong Garai ở Ninh Thuận là một trong những cụm tháp Chăm đẹp và nguyên vẹn nhất còn lại đến ngày nay.", "Văn hóa Chăm"),
    ("Mình vừa thử món cà ri dê của người Chăm An Giang, hương vị đậm đà khó quên. Ai có công thức chuẩn không?", "Ẩm thực Chăm"),
    ("Lễ hội Katê là dịp lễ lớn nhất trong năm của đồng bào Chăm theo đạo Bà La Môn. Năm nay ai đi Ninh Thuận dự không?", "Lễ hội"),
    ("Cho mình hỏi chữ viết Akhar Thrah của người Chăm hiện còn được dạy ở đâu không ạ?", "Hỏi đáp"),
    ("Một ngày lang thang làng gốm Bàu Trúc — làng gốm cổ nhất Đông Nam Á. Ảnh sống ảo cực nghệ.", "Du lịch – Trải nghiệm"),
    ("Chào cả nhà, hôm nay trời đẹp quá, chúc mọi người một ngày an lành!", "Daily"),
]


async def main() -> None:
    settings = get_settings()
    async with lifespan_context(settings) as res:
        users = UserRepository(res.pool)
        repo = CommunityRepository(res.pool)

        created_ids: list[str] = []
        for spec in DEMO_USERS:
            try:
                await res.supa.admin_create_user(spec["email"], spec["password"])
                print(f"  + auth    {spec['username']} <{spec['email']}>")
            except AuthConflictError:
                print(f"  = exists  {spec['username']} <{spec['email']}>")
            except SupabaseError as exc:
                print(f"  ! skip    {spec['email']}: {exc}")
                continue
            profile = await users.get_or_create_by_email(email=spec["email"], username=spec["username"])
            await users.update_profile(
                user_id=profile["id"], username=spec["username"], avatar_url=spec["avatar"]
            )
            created_ids.append(profile["id"])

        if not created_ids:
            print("No demo users available; aborting post seed.")
            return

        stats = await repo.topic_stats()
        if sum(s["post_count"] for s in stats) > 0:
            print("Posts already present; skipping post seed.")
        else:
            for idx, (content, category) in enumerate(DEMO_POSTS):
                author = created_ids[idx % len(created_ids)]
                post_id = await repo.create_post(
                    user_id=author, content=content, category=category, image_urls=[]
                )
                liker = created_ids[(idx + 1) % len(created_ids)]
                await repo.toggle_like(post_id=post_id, user_id=liker)
                if idx % 2 == 0:
                    await repo.add_comment(
                        user_id=liker, post_id=post_id, content="Hay quá, cảm ơn bạn đã chia sẻ!"
                    )
            print(f"Seeded {len(DEMO_POSTS)} posts.")

        print(f"Demo login: {DEMO_USERS[0]['email']} / {DEMO_USERS[0]['password']}")


if __name__ == "__main__":
    asyncio.run(main())
