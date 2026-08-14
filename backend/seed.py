"""Seed demo users and posts so the community feed isn't empty.

Idempotent: running twice won't duplicate the demo accounts.

    python seed.py
"""

import asyncio

from app.auth.service import UserService
from app.community.repository import CommunityRepository
from app.config import get_settings
from app.db import Database

DEMO_USERS = [
    {"email": "minhanh@gmail.com", "username": "Minh Anh", "password": "123Aa", "avatar": "https://i.pravatar.cc/150?img=47"},
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
    db = Database(settings.database_file)
    await db.init()

    users = UserService(db)
    repo = CommunityRepository(db)

    existing = await users.get_by_email(DEMO_USERS[0]["email"])
    if existing is not None:
        print("Demo data already present; skipping seed.")
        return

    created_ids: list[str] = []
    for spec in DEMO_USERS:
        user = await users.create(email=spec["email"], password=spec["password"])
        await users.update_profile(
            user_id=user["id"], username=spec["username"], avatar_url=spec["avatar"]
        )
        created_ids.append(user["id"])
        print(f"  + user {spec['username']} <{spec['email']}>")

    for idx, (content, category) in enumerate(DEMO_POSTS):
        author = created_ids[idx % len(created_ids)]
        post_id = await repo.create_post(
            user_id=author, content=content, category=category, image_urls=[]
        )
        # A couple of likes/comments for realistic stats.
        liker = created_ids[(idx + 1) % len(created_ids)]
        await repo.toggle_like(post_id=post_id, user_id=liker)
        if idx % 2 == 0:
            await repo.add_comment(
                user_id=liker, post_id=post_id, content="Hay quá, cảm ơn bạn đã chia sẻ!"
            )

    print(f"Seeded {len(DEMO_USERS)} users and {len(DEMO_POSTS)} posts.")
    print(f"Demo login: {DEMO_USERS[0]['email']} / {DEMO_USERS[0]['password']}")


if __name__ == "__main__":
    asyncio.run(main())
